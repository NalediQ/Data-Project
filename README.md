# Data-Project
WTC-PQ79PH5F

# Weather ETL Pipeline

A small but complete data engineering project: it **extracts** hourly
forecast data for four South African cities from the free
[Open-Meteo API](https://open-meteo.com/), **transforms** it with pandas
(cleaning, validation, enrichment), and **loads** it into a SQLite
warehouse table — on a schedule, with logging, tests, and idempotent
reruns.

## Why these design choices

- **Open-Meteo** needs no API key, so the project runs with zero setup
  friction, but `extract.py` is written so swapping in a key-based API
  (OpenWeatherMap, etc.) only touches one function.
- **SQLite via SQLAlchemy** keeps the project dependency-free, while the
  SQLAlchemy layer means moving to Postgres later is a one-line
  connection-string change, not a rewrite.
- **Pydantic** validates the raw API response at the extraction
  boundary, so a malformed or changed API response fails loudly and
  early instead of corrupting data three stages downstream.
- **Config-driven**: cities, API settings, and schedule interval all
  live in `config/config.yaml` — adding a fifth city needs no code
  changes.

## Architecture

```
config/config.yaml       cities, API + schedule settings
        │
        ▼
src/extract.py   ──►  Open-Meteo API (requests + tenacity retries)
        │              validated by src/models.py (pydantic)
        ▼
src/transform.py ──►  pandas: clean, dedupe, quality-check, enrich
        │
        ▼
src/load.py      ──►  SQLite (SQLAlchemy): idempotent insert
        │              + pipeline_run_log audit trail
        ▼
src/pipeline.py       orchestrates the three stages, logs the run

main.py           one-off run + summary
scheduler.py      recurring run (hourly by default)
tests/            pytest suite for transform + load + validation
```

### Database schema

**`fact_weather_hourly`** — one row per (location, hour):
`location_name, country, latitude, longitude, timestamp, temperature_c,
temperature_f, humidity_pct, precipitation_mm, wind_speed_kmh,
weather_code, weather_description, is_rainy, ingested_at`

**`pipeline_run_log`** — one row per pipeline execution:
`run_id, started_at, finished_at, status, rows_loaded, error_message`

## Data engineering concerns this project covers

| Concern | Where |
|---|---|
| Extraction from an external API | `src/extract.py` |
| Retry / backoff on transient failures | `tenacity` in `extract.py` |
| Schema validation of raw input | `src/models.py` (pydantic) |
| Transformation with pandas | `src/transform.py` |
| Data quality checks (range checks, dedup) | `src/transform.py` |
| Loading into a database | `src/load.py`, `src/database.py` |
| Idempotent / incremental loads | `load_weather_data()` skips existing keys |
| Orchestration | `src/pipeline.py` |
| Scheduling | `scheduler.py` |
| Logging | `src/logger.py` (loguru, file + console) |
| Run auditability | `pipeline_run_log` table |
| Configuration management | `config/config.yaml`, `.env` |
| Data browsing / inspection |	view_data.py |
| Automated testing | `tests/` (pytest) |
| Documentation | this file |

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional — no key needed for Open-Meteo
```

## Running it

```bash
# One-off run, prints a summary afterwards
python main.py

# Recurring run (hourly by default — set in config.yaml)
python scheduler.py

# View stored data as a clean table in the terminal
python view_data.py
python view_data.py --city "Cape Town" --limit 10
python view_data.py --all-columns

```

## Running the tests

```bash
pytest -v
```

The test suite covers pydantic validation, pandas transformation
(column shape, outlier removal, weather-code mapping, deduplication),
and load idempotency — using an in-memory SQLite database, so tests
never touch `data/weather.db` or the real API.

## Extending it

- Add a city: append it to `config/config.yaml`.
- Add a metric: extend the `hourly` param in `extract.py`'s
  `_build_params`, the `HourlyBlock` model, and the DataFrame build in
  `transform.py`.
- Swap databases: change the connection string in `database.get_engine`.
- Add a dashboard: read from `fact_weather_hourly` with
  `pandas.read_sql` — see 'view_data.py' or `main.py`'s `print_summary()` for the pattern.
