from __future__ import annotations

from typing import Any

import httpx


class ApiError(RuntimeError):
    """Raised for expected external API failures."""


async def get_json(
    url: str,
    *,
    timeout: float,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as exc:
        raise ApiError("request timed out") from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        raise ApiError(f"service returned HTTP {status}") from exc
    except httpx.HTTPError as exc:
        raise ApiError("network request failed") from exc
    except ValueError as exc:
        raise ApiError("service returned invalid JSON") from exc

