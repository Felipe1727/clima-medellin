"""Pruebas de la normalización con las muestras reales de ``samples/``."""

import copy
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from clima_medellin.normalize import NormalizationError, normalize

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
WEATHER_COLUMNS = ["temperature_2m_c", "relative_humidity_2m_pct", "wind_speed_10m_ms"]


def load(name: str) -> dict:
    return json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def era5_end() -> datetime:
    """Fin efectivo de ERA5 el día de la descarga: 00:00 UTC de D-4."""
    today = date.fromisoformat(load("manifest.json")["today_local"])
    return datetime.combine(today - timedelta(days=4), datetime.min.time(), tzinfo=UTC)


FAR_FUTURE = datetime(2100, 1, 1, tzinfo=UTC)


def test_era5_year_sample(era5_end):
    result = normalize("ERA5", load("era5_year.json"), era5_end)
    frame = result.frame
    assert len(frame) == 8664
    assert list(frame.columns) == WEATHER_COLUMNS
    assert str(frame.index.tz) == "UTC"
    assert frame.index.name == "timestamp_utc"
    assert frame.index.is_unique and frame.index.is_monotonic_increasing
    assert frame.index.max() < pd.Timestamp(era5_end)
    assert result.report.received == 8760
    assert result.report.after_effective_end == 96
    assert result.report.rows == 8664


def test_pm25_year_sample():
    result = normalize("CAMS_GLOBAL", load("cams_pm25_year.json"), FAR_FUTURE)
    assert len(result.frame) == 8760
    assert list(result.frame.columns) == ["pm25_ug_m3"]
    assert result.frame["pm25_ug_m3"].notna().all()


def test_recent_month_trailing_nulls_are_cut(era5_end):
    payload = load("era5_recent_month.json")
    result = normalize("ERA5", payload, era5_end)
    assert result.frame.index.max() < pd.Timestamp(era5_end)
    assert result.report.after_effective_end == 4 * 24
    assert result.frame.notna().all().all()


def test_trailing_nulls_are_dropped_even_without_a_cut():
    result = normalize("ERA5", load("era5_recent_month.json"), FAR_FUTURE)
    assert result.report.all_null == 4 * 24
    assert result.frame.notna().any(axis=1).all()


def test_partial_null_is_kept_as_nan_not_zero(era5_end):
    payload = copy.deepcopy(load("era5_year.json"))
    payload["hourly"]["wind_speed_10m"][10] = None
    result = normalize("ERA5", payload, era5_end)
    row = result.frame.loc[pd.Timestamp(payload["hourly"]["time"][10], tz="UTC")]
    assert pd.isna(row["wind_speed_10m_ms"])
    assert row["temperature_2m_c"] == payload["hourly"]["temperature_2m"][10]


def test_out_of_range_value_becomes_null_and_is_counted(era5_end):
    payload = copy.deepcopy(load("era5_year.json"))
    payload["hourly"]["temperature_2m"][20] = 80.0
    result = normalize("ERA5", payload, era5_end)
    row = result.frame.loc[pd.Timestamp(payload["hourly"]["time"][20], tz="UTC")]
    assert pd.isna(row["temperature_2m_c"])
    assert row["relative_humidity_2m_pct"] == payload["hourly"]["relative_humidity_2m"][20]
    assert result.report.out_of_range == {
        "temperature_2m_c": 1,
        "relative_humidity_2m_pct": 0,
        "wind_speed_10m_ms": 0,
    }


def test_intermediate_empty_row_is_dropped(era5_end):
    payload = copy.deepcopy(load("era5_year.json"))
    for name in ("temperature_2m", "relative_humidity_2m", "wind_speed_10m"):
        payload["hourly"][name][30] = None
    result = normalize("ERA5", payload, era5_end)
    assert result.report.all_null == 1
    assert pd.Timestamp(payload["hourly"]["time"][30], tz="UTC") not in result.frame.index


def test_repeated_timestamp_keeps_the_first(era5_end):
    payload = copy.deepcopy(load("era5_year.json"))
    hourly = payload["hourly"]
    hourly["time"].insert(1, hourly["time"][0])
    for name in ("temperature_2m", "relative_humidity_2m", "wind_speed_10m"):
        hourly[name].insert(1, 99.0 if name != "relative_humidity_2m" else 1.0)
    result = normalize("ERA5", payload, era5_end)
    assert result.report.duplicates == 1
    first = result.frame.iloc[0]
    assert first["temperature_2m_c"] == load("era5_year.json")["hourly"]["temperature_2m"][0]


def test_unexpected_unit_fails():
    payload = copy.deepcopy(load("era5_year.json"))
    payload["hourly_units"]["wind_speed_10m"] = "km/h"
    with pytest.raises(NormalizationError, match="wind_speed_10m.*km/h"):
        normalize("ERA5", payload, FAR_FUTURE)


def test_bogota_is_utc_minus_5_all_year():
    """PV-16: America/Bogota no tiene horario de verano en la base de datos tz."""
    hours = pd.date_range("2025-01-01", "2027-01-01", freq="h", tz="UTC")
    offsets = {ts.astimezone(ZoneInfo("America/Bogota")).utcoffset() for ts in hours}
    assert offsets == {timedelta(hours=-5)}
