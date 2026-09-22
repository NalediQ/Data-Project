"""
View weather data from the database as a clean, readable table in the
terminal — an alternative to opening sqlite3 directly.

    python view_data.py                       # latest 20 readings, all cities
    python view_data.py --city "Cape Town"    # filter to one city
    python view_data.py --limit 50            # show more rows
    python view_data.py --all-columns         # show every column, not just the readable subset
"""
from __future__ import annotations

import argparse

import pandas as pd

from src.config import load_config
from src.database import fact_weather_hourly, get_engine

# The columns most useful to glance at — leaves out latitude/longitude,
# temperature_f, and ingested_at, which clutter a terminal view.
DEFAULT_COLUMNS = [
    "location_name",
    "timestamp",
    "temperature_c",
    "humidity_pct",
    "precipitation_mm",
    "wind_speed_kmh",
    "weather_description",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="View weather data from the database.")
    parser.add_argument("--city", help="Filter to a single city (e.g. 'Cape Town').")
    parser.add_argument("--limit", type=int, default=20, help="Max rows to show (default: 20).")
    parser.add_argument(
        "--all-columns", action="store_true",
        help="Show every column instead of the readable subset.",
    )
    return parser.parse_args()


def fetch_data(city: str | None, limit: int) -> pd.DataFrame:
    config = load_config()
    engine = get_engine(config.db_path)

    query = fact_weather_hourly.select().order_by(
        fact_weather_hourly.c.timestamp.desc()
    )
    if city:
        query = query.where(fact_weather_hourly.c.location_name == city)
    query = query.limit(limit)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


def print_table(df: pd.DataFrame, all_columns: bool) -> None:
    if df.empty:
        print("No data found. Have you run `python main.py` yet?")
        return

    if not all_columns:
        df = df[[c for c in DEFAULT_COLUMNS if c in df.columns]]

    # Round floats so columns stay narrow and aligned instead of showing
    # long, uneven decimal tails.
    float_cols = df.select_dtypes(include="float").columns
    df[float_cols] = df[float_cols].round(1)

    print(df.to_string(index=False))
    print(f"\n{len(df)} row(s) shown.")


if __name__ == "__main__":
    args = parse_args()
    data = fetch_data(args.city, args.limit)
    print_table(data, args.all_columns)