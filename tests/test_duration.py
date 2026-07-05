import pytest

from looplet.utils.duration import DurationParseError, format_duration, parse_duration


def test_parse_duration_simple_units() -> None:
    assert parse_duration("30m") == 1800
    assert parse_duration("2h") == 7200
    assert parse_duration("1d") == 86400


def test_parse_duration_combined_units() -> None:
    assert parse_duration("1h30m") == 5400
    assert format_duration(5400) == "1h30m"


@pytest.mark.parametrize("value", ["", "ten", "1x", "1h 30m", "0m", "366d"])
def test_parse_duration_rejects_invalid_values(value: str) -> None:
    with pytest.raises(DurationParseError):
        parse_duration(value)

