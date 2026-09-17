"""
Load layer: writes the transformed DataFrame into the fact table, and
records each pipeline run in pipeline_run_log for auditability.
 
Loads are idempotent: re-running the pipeline for a time range that's
already been loaded will not create duplicate rows, which matters for a
scheduled job that might be re-triggered or re-run after a crash.
"""
from __future__ import annotations
 
from datetime import datetime, timezone
 
import pandas as pd
from sqlalchemy import select
from sqlalchemy.engine import Engine
 
from src.database import fact_weather_hourly, pipeline_run_log
from src.logger import get_logger
 
log = get_logger()
 
 
def _existing_keys(engine: Engine, locations: list[str]) -> set[tuple[str, pd.Timestamp]]:
    if not locations:
        return set()
    with engine.connect() as conn:
        rows = conn.execute(
            select(
                fact_weather_hourly.c.location_name,
                fact_weather_hourly.c.timestamp,
            ).where(fact_weather_hourly.c.location_name.in_(locations))
        ).fetchall()
    return {(r.location_name, pd.Timestamp(r.timestamp)) for r in rows}
 
