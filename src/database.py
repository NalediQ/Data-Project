"""
Database layer: owns the SQLAlchemy engine and schema. Using SQLite keeps
the project dependency-free for a student setup, but because everything
goes through SQLAlchemy, swapping in Postgres later is a one-line change
to the connection string.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)

metadata = MetaData()

fact_weather_hourly = Table(
    "fact_weather_hourly",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("location_name", String, nullable=False),
    Column("country", String, nullable=False),
    Column("latitude", Float, nullable=False),
    Column("longitude", Float, nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("temperature_c", Float, nullable=False),
    Column("temperature_f", Float, nullable=False),
    Column("humidity_pct", Float, nullable=False),
    Column("precipitation_mm", Float, nullable=False),
    Column("wind_speed_kmh", Float, nullable=False),
    Column("weather_code", Integer, nullable=False),
    Column("weather_description", String, nullable=False),
    Column("is_rainy", Boolean, nullable=False),
    Column("ingested_at", DateTime, nullable=False),
)

pipeline_run_log = Table(
    "pipeline_run_log",
    metadata,
    Column("run_id", Integer, primary_key=True, autoincrement=True),
    Column("started_at", DateTime, nullable=False),
    Column("finished_at", DateTime, nullable=True),
    Column("status", String, nullable=False),  # RUNNING | SUCCESS | FAILED
    Column("rows_loaded", Integer, nullable=True),
    Column("error_message", String, nullable=True),
)


def get_engine(db_path: Path):
    engine = create_engine(f"sqlite:///{db_path}")
    metadata.create_all(engine)
    return engine
