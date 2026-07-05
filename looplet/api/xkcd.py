from __future__ import annotations

import random
from dataclasses import dataclass

from looplet.api.base import ApiError, get_json

LATEST_URL = "https://xkcd.com/info.0.json"


@dataclass(frozen=True)
class XkcdComic:
    number: int
    title: str
    image_url: str
    alt: str


async def fetch_xkcd(selector: str, *, timeout: float) -> XkcdComic:
    selector = selector.strip().lower()
    if selector in {"", "latest"}:
        data = await get_json(LATEST_URL, timeout=timeout)
    elif selector == "random":
        latest = await get_json(LATEST_URL, timeout=timeout)
        latest_number = int(latest["num"])
        number = random.randint(1, latest_number)
        data = await get_json(f"https://xkcd.com/{number}/info.0.json", timeout=timeout)
    else:
        try:
            number = int(selector)
        except ValueError as exc:
            raise ApiError("use /xkcd latest, /xkcd random, or /xkcd <number>") from exc
        if number <= 0:
            raise ApiError("comic number must be positive")
        data = await get_json(f"https://xkcd.com/{number}/info.0.json", timeout=timeout)

    try:
        return XkcdComic(
            number=int(data["num"]),
            title=str(data["title"]),
            image_url=str(data["img"]),
            alt=str(data.get("alt", "")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError("xkcd response was incomplete") from exc

