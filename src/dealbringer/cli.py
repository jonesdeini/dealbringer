import argparse
import json
import sqlite3
import sys
from dataclasses import asdict

from dealbringer.config import data_directory
from dealbringer.history import History
from dealbringer.runner import run
from dealbringer.stores.base import StoreError
from dealbringer.stores.fake import FakeStore
from dealbringer.stores.wegmans import unavailable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dealbringer")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stores")
    job = commands.add_parser("run")
    job.add_argument("store", choices=["fake", "wegmans"])
    job.add_argument("--dry-run", action="store_true")
    commands.add_parser("history")
    args = parser.parse_args(argv)
    if args.command == "stores":
        print("fake: available (offline)\nwegmans: unavailable (pending permitted integration)")
        return 0
    try:
        if args.command == "run" and args.store == "wegmans":
            unavailable()
        directory = data_directory()
        history = History(directory)
        if args.command == "history":
            print(json.dumps(history.recent(), indent=2))
            return 0
        result = run(FakeStore(directory), dry_run=args.dry_run)
        history.save(result)
        print(json.dumps(asdict(result), indent=2))
        return 1 if result.errors or result.failed else 0
    except (StoreError, OSError, ValueError, sqlite3.Error) as exc:
        # Do not echo exception contents: future adapters may include sensitive data.
        message = (
            str(exc) if isinstance(exc, StoreError) else "Check local data files and permissions."
        )
        print(f"dealbringer: {message}", file=sys.stderr)
        return 2
