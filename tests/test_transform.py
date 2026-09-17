from src.transform import transform_all


def test_transform_produces_expected_columns(sample_location, sample_response):
    df = transform_all([sample_location], {sample_location.name: sample_response})

    expected_cols = {
        "timestamp", "temperature_c", "humidity_pct", "precipitation_mm",
        "wind_speed_kmh", "weather_code", "location_name", "country",
        "latitude", "longitude", "weather_description", "temperature_f",
        "is_rainy", "ingested_at",
    }
    assert expected_cols.issubset(df.columns)


def test_transform_drops_outlier_rows(sample_location, sample_response):
    # fixture's third reading is 200.0C, which is outside the plausible range
    df = transform_all([sample_location], {sample_location.name: sample_response})
    assert (df["temperature_c"] <= 55).all()
    assert len(df) == 2  # 3 input rows, 1 dropped


def test_transform_maps_weather_codes(sample_location, sample_response):
    df = transform_all([sample_location], {sample_location.name: sample_response})
    row = df[df["weather_code"] == 61].iloc[0]
    assert row["weather_description"] == "Rain"
    assert row["is_rainy"]


def test_transform_handles_no_data():
    df = transform_all([], {})
    assert df.empty


def test_transform_deduplicates(sample_location, sample_response):
    # Same location/response fed in twice should not double the rows
    df = transform_all(
        [sample_location, sample_location],
        {sample_location.name: sample_response},
    )
    assert len(df) == 2  # not 4
