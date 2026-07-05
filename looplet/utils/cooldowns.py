from __future__ import annotations

import time
from collections.abc import Hashable


class CooldownManager:
    def __init__(self, default_seconds: int) -> None:
        self.default_seconds = default_seconds
        self._last_seen: dict[Hashable, float] = {}

    def hit(
        self,
        key: Hashable,
        *,
        cooldown_seconds: int | None = None,
        now: float | None = None,
    ) -> float | None:
        now = now if now is not None else time.monotonic()
        cooldown = cooldown_seconds if cooldown_seconds is not None else self.default_seconds
        previous = self._last_seen.get(key)
        if previous is not None:
            elapsed = now - previous
            if elapsed < cooldown:
                return cooldown - elapsed
        self._last_seen[key] = now
        return None

