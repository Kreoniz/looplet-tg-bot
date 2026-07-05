from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator


class DatabaseError(RuntimeError):
    """Raised when the SQLite database cannot be opened."""


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path)
        except OSError as exc:
            raise DatabaseError(
                f"Cannot create database directory {self.path.parent}. "
                "Check that the container user can write to it."
            ) from exc
        except sqlite3.OperationalError as exc:
            raise DatabaseError(
                f"Cannot open SQLite database at {self.path}. "
                "If you use a bind mount, make the host directory writable by UID 10001, "
                "or use the default Docker named volume."
            ) from exc
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as connection:
            yield connection
