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
 
def load_weather_data(df: pd.DataFrame, engine: Engine) -> int:
    """Insert only rows not already present, keyed on (location, timestamp)."""
    if df.empty:
        log.warning("Nothing to load — transformed DataFrame is empty.")
        return 0

    existing = _existing_keys(engine, df["location_name"].unique().tolist())
    new_mask = ~df.apply(
        lambda r: (r["location_name"], r["timestamp"]) in existing, axis=1
    )
    new_rows = df[new_mask]

    if new_rows.empty:
        log.info("No new rows to load — data already up to date.")
        return 0

    new_rows.to_sql(
        fact_weather_hourly.name, engine, if_exists="append", index=False
    )
    log.info(f"Loaded {len(new_rows)} new rows into {fact_weather_hourly.name}.")
    return len(new_rows)


def start_run(engine: Engine) -> int:
    with engine.begin() as conn:
        result = conn.execute(
            pipeline_run_log.insert().values(
                started_at=datetime.now(timezone.utc),
                status="RUNNING",
            )
        )
        return result.inserted_primary_key[0]


def finish_run(
    engine: Engine, run_id: int, status: str, rows_loaded: int = 0, error_message: str | None = None
) -> None:
    with engine.begin() as conn:
        conn.execute(
            pipeline_run_log.update()
            .where(pipeline_run_log.c.run_id == run_id)
            .values(
                finished_at=datetime.now(timezone.utc),
                status=status,
                rows_loaded=rows_loaded,
                error_message=error_message,
            )
        )
