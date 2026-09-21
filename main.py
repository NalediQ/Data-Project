"""
Run the pipeline once from the command line:
python main.py
After loading, prints a quick summary so you can see the pipeline
actually did something without needing a separate DB browser.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import select

from src.config import load_config
from src.database import fact_weather_hourly, get_engine
from src.pipeline import run_pipeline


def print_summary() -> None:
    config = load_config()
    engine = get_engine(config.db_path)
    with engine.connect() as conn:
        df = pd.read_sql(select(fact_weather_hourly), conn)

    if df.empty:
        print("No data in the database yet.")
        return

    print(f"\nTotal rows in fact_weather_hourly: {len(df)}")
    print("\nLatest reading per location:")
    latest = df.sort_values("timestamp").groupby("location_name").tail(1)
    print(
        latest[
            ["location_name", "timestamp", "temperature_c", "weather_description"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    run_pipeline()
    print_summary()
