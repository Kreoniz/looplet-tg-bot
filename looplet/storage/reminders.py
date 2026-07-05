from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from looplet.storage.db import Database


@dataclass(frozen=True)
class Reminder:
    id: int
    chat_id: int
    user_id: int | None
    text: str
    due_at: datetime
    created_at: datetime
    sent_at: datetime | None


class ReminderStore:
    def __init__(self, database_path: Path | str) -> None:
        self.database = Database(database_path)

    def initialize(self) -> None:
        with self.database.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER,
                    text TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sent_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_reminders_pending
                    ON reminders(sent_at, due_at);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def add_reminder(
        self,
        *,
        chat_id: int,
        user_id: int | None,
        text: str,
        due_at: datetime,
    ) -> int:
        created_at = datetime.now(UTC)
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reminders(chat_id, user_id, text, due_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    user_id,
                    text,
                    _serialize_datetime(due_at),
                    _serialize_datetime(created_at),
                ),
            )
            return int(cursor.lastrowid)

    def get_reminder(self, reminder_id: int) -> Reminder | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM reminders WHERE id = ?",
                (reminder_id,),
            ).fetchone()
        return _row_to_reminder(row) if row is not None else None

    def pending_reminders(self) -> list[Reminder]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM reminders
                WHERE sent_at IS NULL
                ORDER BY due_at ASC
                """
            ).fetchall()
        return [_row_to_reminder(row) for row in rows]

    def due_reminders(self, now: datetime | None = None) -> list[Reminder]:
        now = now or datetime.now(UTC)
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM reminders
                WHERE sent_at IS NULL AND due_at <= ?
                ORDER BY due_at ASC
                """,
                (_serialize_datetime(now),),
            ).fetchall()
        return [_row_to_reminder(row) for row in rows]

    def mark_sent(self, reminder_id: int, sent_at: datetime | None = None) -> None:
        sent_at = sent_at or datetime.now(UTC)
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE reminders SET sent_at = ? WHERE id = ?",
                (_serialize_datetime(sent_at), reminder_id),
            )

    def set_setting(self, key: str, value: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO settings(key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_setting(self, key: str) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,),
            ).fetchone()
        return str(row["value"]) if row is not None else None


def _serialize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _row_to_reminder(row: object) -> Reminder:
    return Reminder(
        id=int(row["id"]),
        chat_id=int(row["chat_id"]),
        user_id=int(row["user_id"]) if row["user_id"] is not None else None,
        text=str(row["text"]),
        due_at=_parse_datetime(row["due_at"]),
        created_at=_parse_datetime(row["created_at"]),
        sent_at=_parse_datetime(row["sent_at"]),
    )

