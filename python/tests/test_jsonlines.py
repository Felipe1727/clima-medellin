"""Pruebas de la conversión DataFrame ↔ JSON Lines."""

import json

import numpy as np
import pandas as pd

from clima_medellin.jsonlines import read_frame, write_frame


def weather_frame() -> pd.DataFrame:
    index = pd.DatetimeIndex(
        pd.to_datetime(["2026-03-01T13:00", "2026-03-01T14:00"], utc=True), name="timestamp_utc"
    )
    return pd.DataFrame(
        {
            "temperature_2m_c": [21.4, 22.0],
            "relative_humidity_2m_pct": [78.0, np.nan],
            "wind_speed_10m_ms": [np.nan, 1.25],
        },
        index=index,
    )


def test_write_uses_z_suffix_and_null(tmp_path):
    path = tmp_path / "staging" / "lote.jsonl"
    assert write_frame(weather_frame(), "ERA5", "MED-CENTRO", path) == 2
    first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert first == {
        "location_code": "MED-CENTRO",
        "source": "ERA5",
        "timestamp_utc": "2026-03-01T13:00:00Z",
        "temperature_2m_c": 21.4,
        "relative_humidity_2m_pct": 78.0,
        "wind_speed_10m_ms": None,
    }


def test_read_builds_utc_index_and_keeps_nan(tmp_path):
    path = tmp_path / "lote.jsonl"
    write_frame(weather_frame(), "ERA5", "MED-CENTRO", path)
    frame = read_frame(path, "ERA5")
    pd.testing.assert_frame_equal(frame, weather_frame())
    assert str(frame.index.tz) == "UTC"


def test_read_keeps_batch_id_when_present(tmp_path):
    path = tmp_path / "export.jsonl"
    path.write_text(
        '{"location_code":"MED-CENTRO","source":"CAMS_GLOBAL",'
        '"timestamp_utc":"2026-03-01T00:00:00Z","pm25_ug_m3":12.3,"batch_id":"abc"}\n',
        encoding="utf-8",
    )
    frame = read_frame(path, "CAMS_GLOBAL")
    assert list(frame.columns) == ["pm25_ug_m3", "batch_id"]
    assert frame.iloc[0]["batch_id"] == "abc"
