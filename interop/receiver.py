"""Receive explicitly approved files into a durable local continuation inbox."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path
from re import fullmatch

from .contract import STREAM_FIELDS, RecordError, check_record, parse_record, read_bytes


CREATE_RECEIPTS = """
    CREATE TABLE IF NOT EXISTS continuation_receipts (
        goal_id TEXT NOT NULL,
        producer TEXT NOT NULL,
        recipient TEXT NOT NULL,
        revision INTEGER NOT NULL,
        sha256 TEXT NOT NULL,
        received_at TEXT NOT NULL,
        payload BLOB NOT NULL,
        PRIMARY KEY (goal_id, producer, recipient, revision)
    ) WITHOUT ROWID
"""

SELECT_LATEST = """
    SELECT revision, sha256, received_at, payload FROM continuation_receipts
    WHERE goal_id = ? AND producer = ? AND recipient = ?
    ORDER BY revision DESC LIMIT 1
"""


def receipt_record(row, stream):
    payload = row["payload"]
    if not isinstance(payload, bytes) or sha256(payload).hexdigest() != row["sha256"]:
        raise RecordError("stored checkpoint digest does not match its receipt")
    record = parse_record(payload)
    if tuple(record[field] for field in STREAM_FIELDS) != stream or record["revision"] != row["revision"]:
        raise RecordError("stored checkpoint identity does not match its receipt")
    return record


def receive_file(database, source, producer, recipient, approved_sha256):
    """Store one exact approved file. Caller supplies the trusted route and digest."""
    if not fullmatch(r"[0-9a-fA-F]{64}", approved_sha256):
        raise RecordError("approved digest must be a SHA-256 hex string")
    payload = read_bytes(source)
    digest = sha256(payload).hexdigest()
    if not compare_digest(digest, approved_sha256.lower()):
        raise RecordError("file digest does not match the approved SHA-256")

    record = parse_record(payload)
    if record["producer"] != producer:
        raise RecordError("record producer does not match the approved route")
    check_record(record, recipient)
    stream = (record["goal_id"], producer, recipient)

    # Give a newly created inbox owner-only permissions, without modifying an existing file.
    database = Path(database)
    try:
        descriptor = os.open(database, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if database.is_symlink() or not database.is_file():
            raise RecordError("continuation inbox must be a regular file in a trusted directory")
    else:
        os.close(descriptor)

    with closing(sqlite3.connect(database, timeout=30)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(CREATE_RECEIPTS)
        previous = connection.execute(SELECT_LATEST, stream).fetchone()
        previous_record = receipt_record(previous, stream) if previous else None
        disposition = check_record(record, recipient, previous_record)
        if disposition == "duplicate":
            if not compare_digest(digest, previous["sha256"]):
                raise RecordError("record bytes conflict with the accepted revision")
            received_at = previous["received_at"]
        else:
            received_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
            connection.execute(
                "INSERT INTO continuation_receipts VALUES (?, ?, ?, ?, ?, ?, ?)",
                (*stream, record["revision"], digest, received_at, payload),
            )
    return {
        "goal_id": record["goal_id"],
        "producer": producer,
        "recipient": recipient,
        "revision": record["revision"],
        "sha256": digest,
        "received_at": received_at,
        "disposition": disposition,
    }


def latest_record(database, goal_id, producer, recipient):
    """Read the exact bytes of the most recent accepted file."""
    database = Path(database)
    if database.is_symlink() or not database.is_file():
        raise RecordError("continuation inbox must be a regular file in a trusted directory")
    uri = f"{database.resolve().as_uri()}?mode=ro"
    stream = (goal_id, producer, recipient)
    with closing(sqlite3.connect(uri, uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(SELECT_LATEST, stream).fetchone()
    if row is None:
        raise RecordError("no accepted checkpoint for this continuation stream")
    receipt_record(row, stream)
    return row["payload"]
