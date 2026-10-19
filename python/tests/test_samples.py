"""Propiedades de las respuestas de muestra guardadas en ``samples/`` (sin red)."""

import json
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
WEATHER_VARIABLES = ("temperature_2m", "relative_humidity_2m", "wind_speed_10m")


def load(name: str) -> dict:
    return json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest() -> dict:
    return load("manifest.json")


def assert_hourly_gmt(payload: dict) -> list[datetime]:
    """Comprueba la zona GMT y que los timestamps son horarios y consecutivos."""
    assert payload["timezone"] == "GMT"
    assert payload["utc_offset_seconds"] == 0
    times = [datetime.fromisoformat(t) for t in payload["hourly"]["time"]]
    steps = {b - a for a, b in zip(times, times[1:], strict=False)}
    assert steps == {timedelta(hours=1)}
    return times


def test_manifest_lists_all_samples(manifest):
    files = {item["file"] for item in manifest["samples"]}
    assert files == {
        "era5_year.json",
        "era5_recent_month.json",
        "cams_pm25_year.json",
        "cams_pm25_last_week.json",
    }
    for item in manifest["samples"]:
        assert (SAMPLES_DIR / item["file"]).is_file()
        assert item["url"].startswith("https://")


def test_era5_year_is_hourly_with_expected_units():
    payload = load("era5_year.json")
    times = assert_hourly_gmt(payload)
    assert len(times) in (8760, 8784)
    assert payload["hourly_units"] == {
        "time": "iso8601",
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "m/s",
    }


def test_pm25_year_has_24_values_per_day_without_nulls():
    payload = load("cams_pm25_year.json")
    times = assert_hourly_gmt(payload)
    assert len(times) in (8760, 8784)
    assert payload["hourly_units"]["pm2_5"] in ("μg/m³", "µg/m³")
    per_day = Counter(t.date() for t in times)
    assert set(per_day.values()) == {24}
    assert all(value is not None for value in payload["hourly"]["pm2_5"])


def test_pm25_last_week_is_hourly():
    payload = load("cams_pm25_last_week.json")
    assert len(assert_hourly_gmt(payload)) == 7 * 24


def test_era5_recent_month_has_trailing_nulls_from_d_minus_4(manifest):
    payload = load("era5_recent_month.json")
    times = assert_hourly_gmt(payload)
    today_local = date.fromisoformat(manifest["today_local"])
    cutoff = datetime.combine(today_local - timedelta(days=4), datetime.min.time())
    for name in WEATHER_VARIABLES:
        values = payload["hourly"][name]
        before = [v for t, v in zip(times, values, strict=True) if t < cutoff]
        after = [v for t, v in zip(times, values, strict=True) if t >= cutoff]
        assert after and all(v is None for v in after), name
        assert before and all(v is not None for v in before), name
