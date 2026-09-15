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