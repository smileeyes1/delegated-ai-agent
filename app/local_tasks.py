"""Durable execution of read-only, deterministic workspace operations."""

from contextlib import closing, contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile


OPERATIONS = ("verify-json", "sha256")
MAX_FILE_BYTES = 16 * 1024 * 1024
HAS_CONFINED_FILE_READS = os.open in os.supports_dir_fd and all(
    hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
)
JSON_TYPES = {
    dict: "object",
    list: "array",
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    type(None): "null",
}


class TaskExecutionError(Exception):
    """An anticipated failure to read or verify the task's input."""


def _reject_non_json_constant(value: str) -> None:
    raise ValueError(f"{value} is outside the JSON grammar")


def _relative_input_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.anchor or not path.parts or ".." in path.parts or "\x00" in str(path):
        raise ValueError("task file must be specified relative to the workspace")
    return path


def _read_workspace_file(workspace: Path, relative_path: str) -> bytes:
    if not HAS_CONFINED_FILE_READS:
        raise TaskExecutionError("secure workspace file reads are unavailable on this platform")
    directory_mode = getattr(os, "O_PATH", getattr(os, "O_SEARCH", os.O_RDONLY))
    directory_flags = directory_mode | os.O_DIRECTORY | os.O_NOFOLLOW
    input_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_NOCTTY", 0)
    try:
        path = _relative_input_path(relative_path)
        directory = os.open(workspace.anchor, directory_flags)
        try:
            for component in (*workspace.parts[1:], *path.parts[:-1]):
                parent = directory
                directory = os.open(component, directory_flags, dir_fd=parent)
                os.close(parent)
            descriptor = os.open(path.name, input_flags, dir_fd=directory)
        finally:
            os.close(directory)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise TaskExecutionError("workspace input must be a regular file")
            with os.fdopen(descriptor, "rb", closefd=False) as source:
                return source.read(MAX_FILE_BYTES + 1)
        finally:
            os.close(descriptor)
    except (OSError, ValueError) as error:
        raise TaskExecutionError("could not safely read the workspace input file") from error


def _execute(workspace: Path, operation: str, relative_path: str) -> dict:
    content = _read_workspace_file(workspace, relative_path)
    if len(content) > MAX_FILE_BYTES:
        raise TaskExecutionError(f"input exceeds {MAX_FILE_BYTES} bytes")

    result = {"bytes": len(content), "sha256": sha256(content).hexdigest()}
    if operation == "verify-json":
        try:
            document = json.loads(content, parse_constant=_reject_non_json_constant)
        except (ValueError, RecursionError) as error:
            raise TaskExecutionError("input is not valid JSON") from error
        result["json_type"] = JSON_TYPES[type(document)]
    return result


class TaskStore:
    """A queue, history, and result store sharing one SQLite transaction boundary.

    A worker holds the write transaction while doing a bounded, read-only
    operation. Completion or failure evidence commits with the task state.
    A worker interrupted before commit leaves the previous state intact.
    """

    def __init__(self, database: Path, workspace: Path):
        self.workspace = Path(workspace).resolve(strict=True)
        if not self.workspace.is_dir():
            raise ValueError("workspace must be a directory")
        self.database = Path(database).resolve()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect(write=True) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS queue_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO queue_metadata VALUES ('workspace', ?)", (str(self.workspace),)
            )
            stored_workspace = connection.execute("SELECT value FROM queue_metadata WHERE key = 'workspace'").fetchone()
            if stored_workspace["value"] != str(self.workspace):
                raise ValueError("queue belongs to a different workspace")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    sequence INTEGER PRIMARY KEY,
                    id TEXT NOT NULL UNIQUE,
                    operation TEXT NOT NULL CHECK (operation IN ('verify-json', 'sha256')),
                    input_path TEXT NOT NULL,
                    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 4),
                    max_attempts INTEGER NOT NULL CHECK (max_attempts BETWEEN 1 AND 10),
                    attempt_limit INTEGER NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending', 'completed', 'failed')),
                    result TEXT
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS task_events (
                    sequence INTEGER PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES tasks(id),
                    timestamp TEXT NOT NULL,
                    event TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    result TEXT
                )
            """)

    @contextmanager
    def _connect(self, *, write: bool = False):
        with closing(sqlite3.connect(self.database, timeout=30)) as connection, connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection

    @staticmethod
    def _event(connection, task_id: str, event: str, attempt: int, result: str | None = None) -> None:
        connection.execute(
            "INSERT INTO task_events (task_id, timestamp, event, attempt, result) VALUES (?, ?, ?, ?, ?)",
            (task_id, datetime.now(timezone.utc).isoformat(), event, attempt, result),
        )

    @staticmethod
    def _read(connection, task_id: str) -> sqlite3.Row:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"unknown task {task_id!r}")
        return row

    @staticmethod
    def _as_dict(row: sqlite3.Row) -> dict:
        record = {key: row[key] for key in row.keys() if key != "sequence"}
        record["result"] = json.loads(record["result"]) if record["result"] is not None else None
        return record

    def enqueue(
        self, task_id: str, operation: str, relative_path: str, priority: int = 2, max_attempts: int = 3
    ) -> dict:
        if not task_id or task_id != task_id.strip() or len(task_id) > 128:
            raise ValueError("task ID must contain 1–128 characters without surrounding whitespace")
        if operation not in OPERATIONS:
            raise ValueError(f"unknown local operation {operation!r}")
        path = _relative_input_path(relative_path)
        if not 1 <= priority <= 4 or not 1 <= max_attempts <= 10:
            raise ValueError("priority must be 1–4 and max attempts must be 1–10")
        with self._connect(write=True) as connection:
            spec = (operation, path.as_posix(), priority, max_attempts)
            inserted = connection.execute(
                """INSERT INTO tasks (id, operation, input_path, priority, max_attempts, attempt_limit)
                   VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING""",
                (task_id, *spec, max_attempts),
            )
            row = self._read(connection, task_id)
            if (row["operation"], row["input_path"], row["priority"], row["max_attempts"]) != spec:
                raise ValueError(f"task ID {task_id!r} already has a different specification")
            if inserted.rowcount:
                self._event(connection, task_id, "enqueued", 0)
            return self._as_dict(row)

    def run_next(self) -> dict | None:
        with self._connect(write=True) as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE state = 'pending' ORDER BY priority DESC, sequence LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            task_id = row["id"]
            attempt = row["attempts"] + 1
            try:
                result = _execute(self.workspace, row["operation"], row["input_path"])
                state, event = "completed", "completed"
            except TaskExecutionError as error:
                result = {"error": str(error)}
                state = "pending" if attempt < row["attempt_limit"] else "failed"
                event = "retry_pending" if state == "pending" else "failed"

            serialized = json.dumps(result, allow_nan=False)
            connection.execute(
                "UPDATE tasks SET state = ?, attempts = ?, result = ? WHERE id = ?",
                (state, attempt, serialized, task_id),
            )
            self._event(connection, task_id, event, attempt, serialized)
            return self._as_dict(self._read(connection, task_id))

    def drain(self, limit: int) -> list[dict]:
        if not 1 <= limit <= 100:
            raise ValueError("drain limit must be 1–100 attempts")
        results = []
        for _ in range(limit):
            result = self.run_next()
            if result is None:
                break
            results.append(result)
        return results

    def status(self, task_id: str | None = None) -> dict | list[dict]:
        with self._connect() as connection:
            if task_id is not None:
                return self._as_dict(self._read(connection, task_id))
            rows = connection.execute("SELECT * FROM tasks ORDER BY priority DESC, sequence")
            return [self._as_dict(row) for row in rows]

    def history(self, task_id: str) -> list[dict]:
        with self._connect() as connection:
            self._read(connection, task_id)
            rows = connection.execute("SELECT * FROM task_events WHERE task_id = ? ORDER BY sequence", (task_id,))
            return [self._as_dict(row) for row in rows]

    def retry(self, task_id: str) -> dict:
        with self._connect(write=True) as connection:
            row = self._read(connection, task_id)
            if row["state"] != "failed":
                raise ValueError("retry requires a failed task")
            connection.execute("UPDATE tasks SET state = 'pending', attempt_limit = attempts + 1 WHERE id = ?", (task_id,))
            self._event(connection, task_id, "requeued", row["attempts"])
            return self._as_dict(self._read(connection, task_id))

    def backup(self, destination: Path) -> Path:
        """Publish an integrity-checked snapshot without replacing any existing file."""
        destination = Path(destination)
        target = destination.parent.resolve(strict=True) / destination.name
        descriptor, temporary_name = tempfile.mkstemp(prefix=".task-queue-", dir=target.parent)
        staging = Path(temporary_name)
        os.close(descriptor)
        try:
            with self._connect() as source, closing(sqlite3.connect(staging)) as snapshot:
                source.backup(snapshot)
                if snapshot.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                    raise sqlite3.DatabaseError("queue snapshot failed its integrity check")
            os.link(staging, target)
        finally:
            staging.unlink(missing_ok=True)
        return target
