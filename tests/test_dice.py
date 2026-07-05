import pytest

from looplet.utils.dice import DiceParseError, format_roll, roll_dice


def test_roll_dice_defaults_to_one_die() -> None:
    result = roll_dice("d20")

    assert result.count == 1
    assert result.sides == 20
    assert 1 <= result.total <= 20


def test_roll_dice_accepts_count_and_sides() -> None:
    result = roll_dice("2d6")

    assert result.expression == "2d6"
    assert len(result.rolls) == 2
    assert 2 <= result.total <= 12
    assert format_roll(result).startswith("2d6:")


@pytest.mark.parametrize("expression", ["", "abc", "0d6", "2d1", "101d6"])
def test_roll_dice_rejects_invalid_expressions(expression: str) -> None:
    with pytest.raises(DiceParseError):
        roll_dice(expression)

