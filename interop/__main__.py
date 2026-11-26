"""Check portable Hakim continuation records without running their contents."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from re import fullmatch
from unicodedata import category


CHANNELS = ("hakim", "dot", "chatgpt-work", "automation")
STATUSES = ("active", "waiting", "blocked", "complete", "cancelled")
TEXT_FIELDS = ("goal_label", "stage", "last_verified", "next_step", "blocker")
FIELDS = {
    "schema", "producer", "recipient", "goal_id", "revision", "updated_at", "status",
    *TEXT_FIELDS,
}
STREAM_FIELDS = ("goal_id", "producer", "recipient")
MAX_BYTES = 16_384
MAX_REVISION = 9_007_199_254_740_991  # Largest exact JSON integer in JavaScript.


class RecordError(ValueError):
    """The handoff could not be accepted as continuation metadata."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecordError("duplicate JSON member")
        result[key] = value
    return result


def read_record(path):
    with Path(path).open("rb") as source:
        contents = source.read(MAX_BYTES + 1)
    if len(contents) > MAX_BYTES:
        raise RecordError("record exceeds 16384 bytes")
    try:
        record = json.loads(contents.decode("utf-8"), object_pairs_hook=unique_object)
    except RecordError:
        raise
    except (ValueError, RecursionError) as error:
        raise RecordError("invalid UTF-8 JSON record") from error

    if not isinstance(record, dict) or record.keys() != FIELDS:
        raise RecordError("record fields must match the continuation schema")
    if record["schema"] != "hakim.continuation/v1":
        raise RecordError("unsupported continuation schema")
    if record["producer"] not in CHANNELS or record["recipient"] not in CHANNELS:
        raise RecordError("unknown producer or recipient")
    if record["producer"] == record["recipient"]:
        raise RecordError("producer and recipient must differ")
    if record["status"] not in STATUSES:
        raise RecordError("unknown continuation status")

    goal_id = record["goal_id"]
    if not isinstance(goal_id, str) or not fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", goal_id):
        raise RecordError("invalid goal_id")
    revision = record["revision"]
    if type(revision) is not int or not 1 <= revision <= MAX_REVISION:
        raise RecordError("revision must be a positive exact JSON integer")
    timestamp = record["updated_at"]
    utc_pattern = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z"
    if not isinstance(timestamp, str) or not fullmatch(utc_pattern, timestamp):
        raise RecordError("updated_at must use UTC RFC 3339 format")
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise RecordError("updated_at is not a valid timestamp") from error

    for field in TEXT_FIELDS:
        value = record[field]
        if not isinstance(value, str) or len(value) > 500:
            raise RecordError(f"{field} must be a string of at most 500 characters")
        if any(category(character) in {"Cc", "Cs", "Zl", "Zp"} for character in value):
            raise RecordError(f"{field} must be a single line of text")
    if not record["goal_label"].strip() or not record["stage"].strip():
        raise RecordError("goal_label and stage must contain text")
    if record["status"] == "blocked" and not record["blocker"].strip():
        raise RecordError("blocked status requires a blocker")
    if record["status"] in ("complete", "cancelled") and record["next_step"].strip():
        raise RecordError("a closed goal cannot include a next step")
    return record


def check_record(record, recipient, previous=None):
    if record["recipient"] != recipient:
        raise RecordError("record is addressed to a different recipient")
    if previous is None:
        return "new"
    if any(record[field] != previous[field] for field in STREAM_FIELDS):
        raise RecordError("previous record belongs to a different continuation stream")
    if record["revision"] < previous["revision"]:
        raise RecordError("record revision is stale")
    if record["revision"] == previous["revision"]:
        if record != previous:
            raise RecordError("record conflicts with the previous version at the same revision")
        return "duplicate"
    return "advanced"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate a handoff addressed to a local recipient")
    check.add_argument("record", type=Path)
    check.add_argument("--for", dest="recipient", choices=CHANNELS, required=True)
    check.add_argument("--previous", type=Path, help="last accepted record for the same stream")
    args = parser.parse_args()
    try:
        record = read_record(args.record)
        previous = read_record(args.previous) if args.previous else None
        disposition = check_record(record, args.recipient, previous)
    except OSError as error:
        print(f"Cannot read continuation file ({error.strerror}).", file=sys.stderr)
        return 1
    except RecordError as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps({
        "goal_id": record["goal_id"],
        "revision": record["revision"],
        "disposition": disposition,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
