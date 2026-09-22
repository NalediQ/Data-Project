"""
Runs the pipeline on a recurring interval (default: hourly, set in
config.yaml). This simulates the orchestration a real data-engineering
job would get from Airflow/cron, without needing either installed.

    python scheduler.py

Stop with Ctrl+C. For production use, prefer an OS-level cron job or a
proper orchestrator calling `python main.py` instead of a long-running
Python process.
"""
from __future__ import annotations

import time

import schedule

from src.config import load_config
from src.logger import get_logger
from src.pipeline import run_pipeline

log = get_logger()


def job() -> None:
    try:
        run_pipeline()
    except Exception:
        # Already logged inside run_pipeline; keep the scheduler alive
        # rather than letting one bad run kill future scheduled runs.
        log.error("Scheduled run failed — will retry at the next interval.")


def main() -> None:
    config = load_config()
    interval = config.schedule_interval_hours
    log.info(f"Starting scheduler — running every {interval} hour(s). Ctrl+C to stop.")

    job()  # run once immediately on startup
    schedule.every(interval).hours.do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
