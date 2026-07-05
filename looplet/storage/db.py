from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as connection:
            yield connection

