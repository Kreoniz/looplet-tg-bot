from __future__ import annotations


def parse_choices(text: str) -> list[str]:
    options = [option.strip() for option in text.split("|") if option.strip()]
    if len(options) < 2:
        raise ValueError("Usage: /choose option1 | option2 | option3")
    return options

