"""Pruebas de la tabla de análisis."""

from datetime import date

import numpy as np
import pandas as pd

from clima_medellin import paths
from clima_medellin.bridge import JavaBridge
from clima_medellin.config import CAMS_GLOBAL, ERA5
from clima_medellin.coverage import window
from clima_medellin.dataset import COLUMNS, combine, load_window


def utc(*stamps: str) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.to_datetime(list(stamps), utc=True), name="timestamp_utc")


WEATHER = pd.DataFrame(
    {"temperature_2m_c": [20.0], "relative_humidity_2m_pct": [80.0], "wind_speed_10m_ms": [1.0]},
    index=utc("2026-03-01T10:00"),
)
AIR = pd.DataFrame({"pm25_ug_m3": [12.0, 15.0]}, index=utc("2026-03-01T10:00", "2026-03-01T11:00"))


def test_hours_with_a_single_source_are_kept():
    frame = combine(WEATHER, AIR)
    assert list(frame.columns) == COLUMNS
    assert len(frame) == 2
    only_air = frame.loc[pd.Timestamp("2026-03-01T11:00", tz="UTC")]
    assert np.isnan(only_air["temperature_2m_c"]) and only_air["pm25_ug_m3"] == 15.0


def test_load_window_reads_both_sources_from_the_database(tmp_path):
    bridge = JavaBridge(
        tmp_path / "t.odb", staging_dir=tmp_path / "staging", exchange_dir=tmp_path / "exchange"
    )
    assert paths.JAR_PATH.is_file()
    for source, frame, config in (("ERA5", WEATHER, ERA5), ("CAMS_GLOBAL", AIR, CAMS_GLOBAL)):
        bridge.import_frame(
            source,
            frame,
            requested_start=frame.index[0],
            requested_end=frame.index[-1],
            endpoint=config.url,
            params=config.fixed_params,
        )
    loaded = load_window(bridge, window(date(2026, 10, 18)))
    pd.testing.assert_frame_equal(loaded, combine(WEATHER, AIR), check_freq=False)
