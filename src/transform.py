"""
Transformation layer: turns validated API objects into a single tidy
pandas DataFrame, applies data-quality checks, and derives a couple of
analytical columns.
"""
from __future__ import annotations

import pandas as pd

from src.config import Location
from src.logger import get_logger
from src.models import OpenMeteoResponse

log = get_logger()

# Open-Meteo's WMO weather codes, collapsed into a few human-readable buckets.
_WEATHER_CODE_MAP = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle",
    61: "Rain", 63: "Rain", 65: "Rain",
    71: "Snow", 73: "Snow", 75: "Snow",
    80: "Rain showers", 81: "Rain showers", 82: "Rain showers",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}


def _response_to_frame(location: Location, response: OpenMeteoResponse) -> pd.DataFrame:
    hourly = response.hourly
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(hourly.time),
            "temperature_c": hourly.temperature_2m,
            "humidity_pct": hourly.relative_humidity_2m,
            "precipitation_mm": hourly.precipitation,
            "wind_speed_kmh": hourly.wind_speed_10m,
            "weather_code": hourly.weather_code,
        }
    )
    df["location_name"] = location.name
    df["country"] = location.country
    df["latitude"] = location.latitude
    df["longitude"] = location.longitude
    return df

def transform_all(
    locations: list[Location], responses: dict[str, OpenMeteoResponse]
) -> pd.DataFrame:
    """Build one clean, deduplicated DataFrame from every location's response."""
    frames = [
        _response_to_frame(loc, responses[loc.name])
        for loc in locations
        if loc.name in responses
    ]
    if not frames:
        log.warning("No data to transform — every extraction call failed.")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    before = len(df)
    df = df.drop_duplicates(subset=["location_name", "timestamp"])
    if len(df) != before:
        log.info(f"Dropped {before - len(df)} duplicate rows during transform.")

    # Data-quality checks: flag values outside physically plausible ranges
    # rather than silently keeping bad readings.
    quality_mask = (
        df["temperature_c"].between(-40, 55)
        & df["humidity_pct"].between(0, 100)
        & df["precipitation_mm"].ge(0)
        & df["wind_speed_kmh"].ge(0)
    )
    bad_rows = (~quality_mask).sum()
    if bad_rows:
        log.warning(f"Dropping {bad_rows} rows that failed data-quality checks.")
    df = df[quality_mask].copy()

    # Derived / enriched columns
    df["weather_description"] = df["weather_code"].map(_WEATHER_CODE_MAP).fillna("Unknown")
    df["temperature_f"] = (df["temperature_c"] * 9 / 5) + 32
    df["is_rainy"] = df["precipitation_mm"] > 0
    df["ingested_at"] = pd.Timestamp.now("UTC")

    return df.reset_index(drop=True)
