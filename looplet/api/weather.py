from __future__ import annotations

from dataclasses import dataclass

from looplet.api.base import ApiError, get_json

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class WeatherReport:
    city: str
    country: str
    temperature_c: float
    feels_like_c: float | None
    wind_kmh: float | None
    description: str
    today_high_c: float | None
    today_low_c: float | None
    precip_probability: float | None


WEATHER_CODES = {
    0: "clear",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "freezing fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "light freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light showers",
    81: "showers",
    82: "heavy showers",
    85: "light snow showers",
    86: "snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "severe thunderstorm with hail",
}


async def _geocode_city(city: str, *, timeout: float) -> dict[str, object]:
    data = await get_json(
        GEOCODING_URL,
        timeout=timeout,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = data.get("results") or []
    if not results:
        raise ApiError(f"could not find {city!r}")
    return results[0]


async def fetch_weather_report(city: str, *, timeout: float) -> WeatherReport:
    location = await _geocode_city(city, timeout=timeout)
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if latitude is None or longitude is None:
        raise ApiError("geocoding result was incomplete")

    data = await get_json(
        FORECAST_URL,
        timeout=timeout,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": 2,
            "timezone": "auto",
        },
    )
    current = data.get("current") or {}
    daily = data.get("daily") or {}
    if "temperature_2m" not in current:
        raise ApiError("forecast response was incomplete")

    code = int(current.get("weather_code", -1))
    return WeatherReport(
        city=str(location.get("name") or city),
        country=str(location.get("country_code") or location.get("country") or ""),
        temperature_c=float(current["temperature_2m"]),
        feels_like_c=_maybe_float(current.get("apparent_temperature")),
        wind_kmh=_maybe_float(current.get("wind_speed_10m")),
        description=WEATHER_CODES.get(code, f"weather code {code}"),
        today_high_c=_first_float(daily.get("temperature_2m_max")),
        today_low_c=_first_float(daily.get("temperature_2m_min")),
        precip_probability=_first_float(daily.get("precipitation_probability_max")),
    )


def _maybe_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _first_float(value: object) -> float | None:
    if isinstance(value, list) and value:
        return _maybe_float(value[0])
    return None


def _format_temp(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.0f}C"


def format_weather_report(report: WeatherReport) -> str:
    place = f"{report.city}, {report.country}" if report.country else report.city
    lines = [
        f"Weather for {place}: {report.temperature_c:.0f}C, {report.description}.",
        f"Feels like {_format_temp(report.feels_like_c)}; wind {_format_temp(report.wind_kmh).replace('C', ' km/h')}.",
        f"Today: high {_format_temp(report.today_high_c)}, low {_format_temp(report.today_low_c)}.",
    ]
    if report.precip_probability is not None:
        lines.append(f"Precipitation chance: {report.precip_probability:.0f}%.")
    return "\n".join(lines)

