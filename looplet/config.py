from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Raised when environment configuration is missing or invalid."""


def _parse_chat_ids(raw: str | None) -> frozenset[int]:
    if not raw:
        return frozenset()

    chat_ids: set[int] = set()
    for part in raw.split(","):
        value = part.strip()
        if not value:
            continue
        try:
            chat_ids.add(int(value))
        except ValueError as exc:
            raise ConfigError(f"Invalid chat ID in ALLOWED_CHAT_IDS: {value!r}") from exc
    return frozenset(chat_ids)


def _positive_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return value


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    allowed_chat_ids: frozenset[int]
    database_path: Path
    default_city: str
    request_timeout_seconds: float
    external_cooldown_seconds: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or token == "replace-with-your-bot-token":
            raise ConfigError("TELEGRAM_BOT_TOKEN is required")

        default_city = os.getenv("DEFAULT_CITY", "Omsk").strip() or "Omsk"
        database_path = Path(os.getenv("DATABASE_PATH", "data/looplet.sqlite3")).expanduser()

        return cls(
            telegram_bot_token=token,
            allowed_chat_ids=_parse_chat_ids(os.getenv("ALLOWED_CHAT_IDS")),
            database_path=database_path,
            default_city=default_city,
            request_timeout_seconds=_positive_float("REQUEST_TIMEOUT_SECONDS", 8.0),
            external_cooldown_seconds=_positive_int("EXTERNAL_COOLDOWN_SECONDS", 8),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        )

