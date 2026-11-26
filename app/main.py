"""Command-line entry point for the offline task runtime."""

import argparse
import json
from pathlib import Path
import sqlite3

if __package__:
    from .local_tasks import OPERATIONS, TaskStore
else:
    from local_tasks import OPERATIONS, TaskStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="root for task inputs")
    parser.add_argument("--db", type=Path, help="SQLite queue path, default: data/task-runtime.sqlite3 in the workspace")
    commands = parser.add_subparsers(dest="command")

    enqueue = commands.add_parser("enqueue", help="register a task using a stable ID")
    enqueue.add_argument("id")
    enqueue.add_argument("operation", choices=OPERATIONS)
    enqueue.add_argument("file", help="regular file relative to the workspace")
    enqueue.add_argument("--priority", type=int, choices=range(1, 5), default=2)
    enqueue.add_argument("--max-attempts", type=int, choices=range(1, 11), default=3)
    commands.add_parser("run-next", help="execute one queued attempt")
    drain = commands.add_parser("drain", help="execute a bounded number of queued attempts")
    drain.add_argument("--limit", type=int, default=20, help="attempt limit from 1 to 100, default: 20")
    status = commands.add_parser("status", help="display one task or the active queue")
    status.add_argument("id", nargs="?")
    history = commands.add_parser("history", help="display a task's persisted events")
    history.add_argument("id")
    retry = commands.add_parser("retry", help="requeue a failed task for one attempt")
    retry.add_argument("id")
    backup = commands.add_parser("backup", help="write a queue snapshot to a new file")
    backup.add_argument("destination", type=Path)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    try:
        database = args.db if args.db is not None else args.workspace / "data/task-runtime.sqlite3"
        store = TaskStore(database, args.workspace)
        if args.command == "enqueue":
            result = store.enqueue(args.id, args.operation, args.file, args.priority, args.max_attempts)
        elif args.command == "run-next":
            result = store.run_next()
        elif args.command == "drain":
            result = store.drain(args.limit)
        elif args.command == "status":
            result = store.status(args.id)
        elif args.command == "history":
            result = store.history(args.id)
        elif args.command == "retry":
            result = store.retry(args.id)
        else:
            result = {"backup": str(store.backup(args.destination))}
    except (KeyError, ValueError, OSError, sqlite3.Error) as error:
        parser.exit(2, f"error: {error}\n")

    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    if args.command == "run-next" and result is not None and result["state"] != "completed":
        return 1
    if args.command == "drain" and any(attempt["state"] != "completed" for attempt in result):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
