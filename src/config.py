"""
Loads pipeline configuration from config/config.yaml and environment
variables (.env). Centralising config here means nothing else in the
codebase hardcodes a URL, path, or location list.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()  # loads .env into os.environ if present

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


@dataclass(frozen=True)
class Location:
    name: str
    country: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class ApiConfig:
    base_url: str
    timeout_seconds: int
    max_retries: int
    retry_backoff_seconds: int


@dataclass(frozen=True)
class AppConfig:
    api: ApiConfig
    locations: list[Location]
    db_path: Path
    hourly_forecast_days: int
    schedule_interval_hours: int

def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    api = ApiConfig(**raw["api"])
    locations = [Location(**loc) for loc in raw["locations"]]
    db_path = PROJECT_ROOT / raw["database"]["path"]
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        api=api,
        locations=locations,
        db_path=db_path,
        hourly_forecast_days=raw["pipeline"]["hourly_forecast_days"],
        schedule_interval_hours=raw["pipeline"]["schedule_interval_hours"],
    )
