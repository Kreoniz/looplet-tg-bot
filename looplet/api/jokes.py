from __future__ import annotations

from looplet.api.base import ApiError, get_json

JOKE_URL = "https://icanhazdadjoke.com/"


async def fetch_dad_joke(*, timeout: float) -> str:
    data = await get_json(
        JOKE_URL,
        timeout=timeout,
        headers={
            "Accept": "application/json",
            "User-Agent": "LoopletBot/0.1 personal Telegram bot",
        },
    )
    joke = str(data.get("joke", "")).strip()
    if not joke:
        raise ApiError("empty joke response")
    return joke

