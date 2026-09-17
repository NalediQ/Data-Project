import pytest
from pydantic import ValidationError

from src.models import HourlyBlock, OpenMeteoResponse


def test_valid_response_parses(sample_response):
    assert sample_response.latitude == -33.9249
    assert len(sample_response.hourly.time) == 3


def test_missing_field_raises():
    with pytest.raises(ValidationError):
        HourlyBlock(
            time=["2026-09-15T00:00"],
            temperature_2m=[15.2],
            relative_humidity_2m=[80.0],
            precipitation=[0.0],
            # wind_speed_10m missing
            weather_code=[1],
        )


def test_misaligned_arrays_raise_on_validate(sample_response):
    sample_response.hourly.temperature_2m.append(99.9)  # now length 4 vs 3
    with pytest.raises(ValueError):
        sample_response.validate_alignment()
