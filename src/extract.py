"""
Extraction layer: talks to the Open-Meteo API only. Nothing in this
module knows about pandas or the database — it just returns validated
Python objects, which keeps the pipeline stages testable in isolation.
"""

from __future__ import annotations

from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import ApiConfig, Location
from src.logger import get_logger
from src.models import OpenMeteoResponse

log = get_logger()


class ExtractionError(Exception):
    """Raised when the API cannot be reached or returns an unusable payload."""


def _build_params(location: Location, forecast_days: int) -> dict[str, Any]:
    return {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "hourly": (
            "temperature_2m,relative_humidity_2m,precipitation,"
            "wind_speed_10m,weather_code"
        ),
        "forecast_days": forecast_days,
        "timezone": "auto",
    }


def fetch_location_weather(
    location: Location, api_cfg: ApiConfig, forecast_days: int
) -> OpenMeteoResponse:
    """Fetch and validate hourly forecast data for a single location."""

    @retry(
        reraise=True,
        stop=stop_after_attempt(api_cfg.max_retries),
        wait=wait_exponential(multiplier=api_cfg.retry_backoff_seconds),
        retry=retry_if_exception_type(
            (requests.ConnectionError, requests.Timeout, requests.HTTPError)
        ),
    )
    def _call() -> dict:
        response = requests.get(
            api_cfg.base_url,
            params=_build_params(location, forecast_days),
            timeout=api_cfg.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    log.info(f"Fetching weather data for {location.name}")
    try:
        raw = _call()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
        raise ExtractionError(
            f"Failed to fetch data for {location.name} after retries: {exc}"
        ) from exc

    try:
        parsed = OpenMeteoResponse(**raw)
        parsed.validate_alignment()
    except Exception as exc:  # pydantic ValidationError or alignment error
        raise ExtractionError(
            f"Invalid API response for {location.name}: {exc}"
        ) from exc

    return parsed
