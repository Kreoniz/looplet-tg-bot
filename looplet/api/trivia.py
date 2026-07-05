from __future__ import annotations

import html
import random
from dataclasses import dataclass

from looplet.api.base import ApiError, get_json

TRIVIA_URL = "https://opentdb.com/api.php"


@dataclass(frozen=True)
class TriviaQuestion:
    question: str
    options: list[str]
    correct_option_id: int


async def fetch_trivia_question(*, timeout: float) -> TriviaQuestion:
    data = await get_json(
        TRIVIA_URL,
        timeout=timeout,
        params={"amount": 1, "type": "multiple"},
    )
    if data.get("response_code") != 0 or not data.get("results"):
        raise ApiError("no trivia question returned")

    raw = data["results"][0]
    question = html.unescape(str(raw.get("question", ""))).strip()
    correct = html.unescape(str(raw.get("correct_answer", ""))).strip()
    incorrect = [html.unescape(str(value)).strip() for value in raw.get("incorrect_answers", [])]
    options = [correct, *incorrect]
    options = [option for option in options if option]
    if not question or len(options) < 2:
        raise ApiError("trivia response was incomplete")

    random.shuffle(options)
    return TriviaQuestion(
        question=question,
        options=options,
        correct_option_id=options.index(correct),
    )

