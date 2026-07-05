from __future__ import annotations

import random
import re
from dataclasses import dataclass


class DiceParseError(ValueError):
    """Raised when a dice expression cannot be parsed."""


@dataclass(frozen=True)
class RollResult:
    expression: str
    count: int
    sides: int
    rolls: list[int]

    @property
    def total(self) -> int:
        return sum(self.rolls)


DICE_RE = re.compile(r"^(?:(?P<count>\d{1,3})?)d(?P<sides>\d{1,4})$", re.IGNORECASE)


def roll_dice(expression: str) -> RollResult:
    expression = expression.strip().lower()
    match = DICE_RE.fullmatch(expression)
    if not match:
        raise DiceParseError("Usage: /roll 2d6 or /roll d20")

    count = int(match.group("count") or 1)
    sides = int(match.group("sides"))
    if count < 1 or count > 100:
        raise DiceParseError("Dice count must be between 1 and 100.")
    if sides < 2 or sides > 1000:
        raise DiceParseError("Dice sides must be between 2 and 1000.")

    return RollResult(
        expression=f"{count}d{sides}",
        count=count,
        sides=sides,
        rolls=[random.randint(1, sides) for _ in range(count)],
    )


def format_roll(result: RollResult) -> str:
    if result.count == 1:
        return f"{result.expression}: {result.total}"
    if result.count <= 20:
        rolls = ", ".join(str(value) for value in result.rolls)
        return f"{result.expression}: {result.total} ({rolls})"
    return f"{result.expression}: {result.total}"

