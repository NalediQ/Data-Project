import pytest

from src.config import Location
from src.models import HourlyBlock, OpenMeteoResponse


@pytest.fixture
def sample_location() -> Location:
    return Location(name="Cape Town", country="South Africa",
                     latitude=-33.9249, longitude=18.4241)


@pytest.fixture
def sample_response() -> OpenMeteoResponse:
    hourly = HourlyBlock(
        time=["2026-09-15T00:00", "2026-09-15T01:00", "2026-09-15T02:00"],
        temperature_2m=[15.2, 14.8, 200.0],       # last value is an outlier
        relative_humidity_2m=[80.0, 82.0, 81.0],
        precipitation=[0.0, 0.1, 0.0],
        wind_speed_10m=[10.0, 12.5, 9.0],
        weather_code=[1, 61, 0],
    )
    return OpenMeteoResponse(
        latitude=-33.9249, longitude=18.4241, timezone="Africa/Johannesburg",
        hourly=hourly,
    )
