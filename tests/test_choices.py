import pytest

from looplet.utils.choices import parse_choices


def test_parse_choices_splits_pipe_options() -> None:
    assert parse_choices("tea | coffee | water") == ["tea", "coffee", "water"]


def test_parse_choices_requires_two_options() -> None:
    with pytest.raises(ValueError):
        parse_choices("only one")

