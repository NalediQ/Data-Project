"""
Orchestration layer: runs one full extract -> transform -> load cycle
and records the outcome. This is the single entry point both `main.py`
(one-off run) and `scheduler.py` (recurring run) call into.
"""
from __future__ import annotations

from src.config import load_config
from src.database import get_engine
from src.extract import extract_all
from src.load import finish_run, load_weather_data, start_run
from src.logger import get_logger
from src.transform import transform_all

log = get_logger()


def run_pipeline() -> int:
    """Run one full pipeline cycle. Returns the number of rows loaded."""
    config = load_config()
    engine = get_engine(config.db_path)
    run_id = start_run(engine)
    log.info(f"Pipeline run {run_id} started.")

    try:
        raw_responses = extract_all(
            config.locations, config.api, config.hourly_forecast_days
        )
        if not raw_responses:
            raise RuntimeError("Extraction returned no data for any location.")

        clean_df = transform_all(config.locations, raw_responses)
        rows_loaded = load_weather_data(clean_df, engine)

        finish_run(engine, run_id, status="SUCCESS", rows_loaded=rows_loaded)
        log.info(f"Pipeline run {run_id} finished successfully — {rows_loaded} rows loaded.")
        return rows_loaded

    except Exception as exc:
        log.exception(f"Pipeline run {run_id} failed: {exc}")
        finish_run(engine, run_id, status="FAILED", error_message=str(exc))
        raise


if __name__ == "__main__":
    run_pipeline()
