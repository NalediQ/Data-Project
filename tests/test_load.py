import pandas as pd
import pytest
from sqlalchemy import create_engine

from src.database import metadata
from src.load import finish_run, load_weather_data, start_run
from src.transform import transform_all


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    metadata.create_all(eng)
    return eng


@pytest.fixture
def clean_df(sample_location, sample_response):
    return transform_all([sample_location], {sample_location.name: sample_response})


def test_load_inserts_rows(engine, clean_df):
    inserted = load_weather_data(clean_df, engine)
    assert inserted == len(clean_df)


def test_load_is_idempotent(engine, clean_df):
    load_weather_data(clean_df, engine)
    second_run_inserted = load_weather_data(clean_df, engine)
    assert second_run_inserted == 0  # nothing new the second time


def test_load_empty_dataframe_returns_zero(engine):
    assert load_weather_data(pd.DataFrame(), engine) == 0


def test_run_log_lifecycle(engine):
    run_id = start_run(engine)
    finish_run(engine, run_id, status="SUCCESS", rows_loaded=10)

    with engine.connect() as conn:
        row = conn.exec_driver_sql(
            "SELECT status, rows_loaded FROM pipeline_run_log WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    assert row.status == "SUCCESS"
    assert row.rows_loaded == 10
