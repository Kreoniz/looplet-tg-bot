from __future__ import annotations

import random
from importlib import resources


def load_quotes() -> list[str]:
    quotes_file = resources.files("looplet.data").joinpath("quotes.txt")
    quotes = [
        line.strip()
        for line in quotes_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not quotes:
        return ["Keep going; future you is already grateful."]
    return quotes


def random_quote() -> str:
    return random.choice(load_quotes())

