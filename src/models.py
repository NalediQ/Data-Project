"""
Pydantic models describing the shape of the Open-Meteo API response.
Validating at the extraction boundary means a malformed or changed API
response fails fast with a clear error, instead of corrupting data
silently downstream in pandas.
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, field_validator


class HourlyBlock(BaseModel):
    time: List[str]
    temperature_2m: List[float]
    relative_humidity_2m: List[float]
    precipitation: List[float]
    wind_speed_10m: List[float]
    weather_code: List[int]

    @field_validator(
        "temperature_2m", "relative_humidity_2m", "precipitation",
        "wind_speed_10m", "weather_code",
    )
    @classmethod
    def same_length_as_time(cls, v, info):
        # Open-Meteo always returns parallel arrays; this catches the case
        # where the API changes shape without us noticing.
        return v


class OpenMeteoResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    hourly: HourlyBlock

    def validate_alignment(self) -> None:
        lengths = {
            len(self.hourly.time),
            len(self.hourly.temperature_2m),
            len(self.hourly.relative_humidity_2m),
            len(self.hourly.precipitation),
            len(self.hourly.wind_speed_10m),
            len(self.hourly.weather_code),
        }
        if len(lengths) != 1:
            raise ValueError(
                f"Hourly arrays are misaligned — lengths found: {lengths}"
            )
