import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from dealbringer.models import RunResult


class History:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = data_dir / "history.sqlite3"
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, summary TEXT)")
        self.path.chmod(0o600)

    def save(self, result: RunResult) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO runs (summary) VALUES (?)", (json.dumps(asdict(result)),))

    def recent(self, limit: int = 20) -> list[dict]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT summary FROM runs ORDER BY id DESC LIMIT ?", (limit,))
            return [json.loads(row[0]) for row in rows]
