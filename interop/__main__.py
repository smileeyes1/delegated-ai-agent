"""Check and receive portable Hakim continuation records."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .contract import CHANNELS, RecordError, check_record, read_record
from .receiver import latest_record, receive_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate a handoff addressed to a local recipient")
    check.add_argument("record", type=Path)
    check.add_argument("--for", dest="recipient", choices=CHANNELS, required=True)
    check.add_argument("--previous", type=Path, help="last accepted record for the same stream")

    receive = commands.add_parser("receive", help="verify an approved file and store the checkpoint")
    receive.add_argument("record", type=Path)
    receive.add_argument("--sha256", required=True, help="digest supplied by the trusted approval channel")
    latest = commands.add_parser("latest", help="read the last accepted checkpoint in a local stream")
    latest.add_argument("goal_id")
    for command in (receive, latest):
        command.add_argument("--db", type=Path, required=True)
        command.add_argument("--from", dest="producer", choices=CHANNELS, required=True)
        command.add_argument("--for", dest="recipient", choices=CHANNELS, required=True)

    args = parser.parse_args()
    try:
        if args.command == "receive":
            print(json.dumps(receive_file(args.db, args.record, args.producer, args.recipient, args.sha256)))
        elif args.command == "latest":
            sys.stdout.buffer.write(latest_record(args.db, args.goal_id, args.producer, args.recipient))
        else:
            record = read_record(args.record)
            previous = read_record(args.previous) if args.previous else None
            disposition = check_record(record, args.recipient, previous)
            print(json.dumps({
                "goal_id": record["goal_id"],
                "revision": record["revision"],
                "disposition": disposition,
            }))
    except OSError as error:
        print(f"Cannot access continuation file ({error.strerror}).", file=sys.stderr)
        return 1
    except RecordError as error:
        print(error, file=sys.stderr)
        return 1
    except sqlite3.Error:
        print("Cannot access the continuation inbox database.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
