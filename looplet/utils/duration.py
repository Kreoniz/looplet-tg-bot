from __future__ import annotations

import re


class DurationParseError(ValueError):
    """Raised when a duration string is invalid."""


UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 24 * 60 * 60,
    "w": 7 * 24 * 60 * 60,
}
MAX_SECONDS = 365 * 24 * 60 * 60
DURATION_RE = re.compile(r"(?P<value>\d+)(?P<unit>[smhdw])", re.IGNORECASE)


def parse_duration(text: str) -> int:
    text = text.strip().lower()
    if not text:
        raise DurationParseError("Usage: /remind <duration> <text>, for example /remind 30m stretch")

    position = 0
    total = 0
    for match in DURATION_RE.finditer(text):
        if match.start() != position:
            raise DurationParseError("Duration must look like 30m, 2h, 1d, or 1h30m.")
        position = match.end()
        value = int(match.group("value"))
        unit = match.group("unit").lower()
        total += value * UNIT_SECONDS[unit]

    if position != len(text) or total <= 0:
        raise DurationParseError("Duration must look like 30m, 2h, 1d, or 1h30m.")
    if total > MAX_SECONDS:
        raise DurationParseError("Reminder duration cannot be more than 365 days.")
    return total


def format_duration(seconds: int) -> str:
    parts: list[str] = []
    remaining = seconds
    units = [
        ("w", UNIT_SECONDS["w"]),
        ("d", UNIT_SECONDS["d"]),
        ("h", UNIT_SECONDS["h"]),
        ("m", UNIT_SECONDS["m"]),
        ("s", UNIT_SECONDS["s"]),
    ]
    for label, unit_seconds in units:
        amount, remaining = divmod(remaining, unit_seconds)
        if amount:
            parts.append(f"{amount}{label}")
    return "".join(parts) if parts else "0s"

