"""Franjas y perfil diurno, comprobados con un día calculado a mano."""

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from clima_medellin.bands import daily_bands, diurnal_profile
from clima_medellin.split import Split

COLUMNS = ["temperature_2m_c", "pm25_ug_m3"]


def local_day_frame() -> pd.DataFrame:
    """El 12 de abril de 2026 en Medellín: de 05:00 UTC del 12 a 05:00 UTC del 13."""
    index = pd.date_range("2026-04-12 05:00", "2026-04-13 04:00", freq="h", tz="UTC")
    frame = pd.DataFrame({"temperature_2m_c": 20.0, "pm25_ug_m3": 10.0}, index=index)

    def at(local_hour: int) -> pd.Timestamp:
        return pd.Timestamp(2026, 4, 12, local_hour, tz="America/Bogota").tz_convert("UTC")

    # Mañana: ejemplo de la documentación (17,8 / falta / 19,6 → 18,7).
    frame.loc[at(7), "temperature_2m_c"] = 17.8
    frame.loc[at(8), "temperature_2m_c"] = np.nan
    frame.loc[at(9), "temperature_2m_c"] = 19.6
    # Tarde: un solo valor válido → NaN.
    frame.loc[at(14), "temperature_2m_c"] = np.nan
    frame.loc[at(15), "temperature_2m_c"] = np.nan
    # Noche: 19-21 h locales = 00-02 UTC del 13 de abril.
    for hour, value in ((19, 30.0), (20, 31.0), (21, 32.0)):
        frame.loc[at(hour), "pm25_ug_m3"] = value
    return frame


def test_hand_computed_day():
    bands = daily_bands(local_day_frame())
    day = datetime(2026, 4, 12).date()
    assert list(bands.index) == [day]
    assert bands.loc[day, ("temperature_2m_c", "mañana")] == pytest.approx(18.7)
    assert np.isnan(bands.loc[day, ("temperature_2m_c", "tarde")])
    assert bands.loc[day, ("temperature_2m_c", "noche")] == 20.0
    assert bands.loc[day, ("pm25_ug_m3", "noche")] == pytest.approx(31.0)
    assert bands.loc[day, ("pm25_ug_m3", "mañana")] == 10.0


def test_night_band_uses_the_next_utc_day():
    night_utc = pd.date_range("2026-04-13 00:00", periods=3, freq="h", tz="UTC")
    frame = pd.DataFrame({"temperature_2m_c": [1.0, 2.0, 3.0]}, index=night_utc)
    bands = daily_bands(frame)
    assert list(bands.index) == [datetime(2026, 4, 12).date()]
    assert bands.iloc[0][("temperature_2m_c", "noche")] == 2.0


def test_missing_rows_count_as_missing_hours():
    frame = local_day_frame()
    seven_local = pd.Timestamp(2026, 4, 12, 7, tz="America/Bogota").tz_convert("UTC")
    frame = frame.drop(index=seven_local)  # sin fila a las 07:00: solo queda 09:00
    bands = daily_bands(frame)
    assert np.isnan(bands.iloc[0][("temperature_2m_c", "mañana")])


def test_diurnal_profile_uses_only_the_training_period():
    index = pd.date_range("2026-01-01", "2026-01-04 23:00", freq="h", tz="UTC")
    frame = pd.DataFrame({"temperature_2m_c": 10.0, "pm25_ug_m3": 5.0}, index=index)
    split = Split(
        train_start=datetime(2026, 1, 1, 5, tzinfo=UTC),
        train_end=datetime(2026, 1, 2, 5, tzinfo=UTC),
        test_start=datetime(2026, 1, 3, 5, tzinfo=UTC),
        test_end=datetime(2026, 1, 4, 5, tzinfo=UTC),
    )
    frame.loc[split.test(frame).index, "temperature_2m_c"] = 99.0
    frame.loc[pd.Timestamp("2026-01-01 05:00", tz="UTC"), "pm25_ug_m3"] = np.nan

    profile = diurnal_profile(frame, split)

    assert list(profile.index) == list(range(24))
    assert (profile[("temperature_2m_c", "media")] == 10.0).all()
    assert (profile[("temperature_2m_c", "n")] == 1).all()
    assert profile.loc[0, ("pm25_ug_m3", "n")] == 0  # 05:00 UTC = 00:00 local, era nulo
    assert np.isnan(profile.loc[0, ("pm25_ug_m3", "media")])
