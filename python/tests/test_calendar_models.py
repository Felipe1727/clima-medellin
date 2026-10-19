"""Pruebas de los modelos de calendario."""

import json
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from clima_medellin.calendar_models import (
    HOUR_COLUMNS,
    TARGETS,
    PredictionRequestError,
    calendar_features,
    fit_calendar_model,
    fit_calendar_models,
    parse_moment,
    predict,
    request_hours,
)
from clima_medellin.coverage import window
from clima_medellin.dataset import combine
from clima_medellin.normalize import normalize
from clima_medellin.split import temporal_split

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
TODAY = date(2026, 10, 18)
WIN = window(TODAY)
SPLIT = temporal_split(WIN)
HOURS = pd.date_range(WIN.start_utc, WIN.end_utc, freq="h", inclusive="left")
EFFECTS = np.array(
    [
        0,
        -1,
        -2,
        -2.5,
        -2.8,
        -3,
        -3.2,
        -2,
        -1,
        0,
        1,
        2,
        3,
        3.5,
        4,
        4.2,
        4,
        3,
        2,
        1.5,
        1,
        0.5,
        0.2,
        0.1,
    ]
)


def synthetic() -> pd.DataFrame:
    local = HOURS.tz_convert("America/Bogota")
    angle = 2 * np.pi * local.dayofyear.to_numpy() / 365.25
    value = 20 + EFFECTS[local.hour.to_numpy()] + 1 * np.sin(angle) - 2 * np.cos(angle)
    return pd.DataFrame({v: value for v in TARGETS}, index=HOURS)


@pytest.fixture(scope="module")
def sample_frame() -> pd.DataFrame:
    def load(name):
        return json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))

    weather = normalize("ERA5", load("era5_year.json"), datetime(2026, 10, 14, tzinfo=UTC))
    air = normalize("CAMS_GLOBAL", load("cams_pm25_year.json"), WIN.end_utc)
    joined = combine(weather.frame, air.frame)
    return joined[(joined.index >= WIN.start_utc) & (joined.index < WIN.end_utc)]


def test_midnight_has_all_hour_indicators_at_zero():
    midnight = pd.DatetimeIndex([pd.Timestamp("2026-03-15 00:00", tz="America/Bogota")])
    features = calendar_features(midnight.tz_convert("UTC"))
    assert (features[HOUR_COLUMNS].to_numpy() == 0).all()


def test_utc_is_converted_to_local_hour():
    features = calendar_features(pd.DatetimeIndex([pd.Timestamp("2026-03-15T20:00Z")]))
    assert features.loc[:, HOUR_COLUMNS].iloc[0].idxmax() == "h15"
    assert features[HOUR_COLUMNS].to_numpy().sum() == 1


def test_known_hour_effects_and_season_are_recovered():
    model = fit_calendar_model(synthetic(), "temperature_2m_c", SPLIT)
    np.testing.assert_allclose(model.hour_effects.to_numpy(), EFFECTS, atol=1e-6)
    assert model.season_sin == pytest.approx(1, abs=1e-6)
    assert model.season_cos == pytest.approx(-2, abs=1e-6)
    assert model.intercept == pytest.approx(20, abs=1e-6)
    assert model.typical_error == pytest.approx(0, abs=1e-6)


def test_evaluation_does_not_see_the_test_period():
    data = synthetic()
    first = fit_calendar_model(data, "pm25_ug_m3", SPLIT)
    changed = data.copy()
    changed.loc[SPLIT.test(changed).index, "pm25_ug_m3"] += 50
    second = fit_calendar_model(changed, "pm25_ug_m3", SPLIT)
    # La línea base y el modelo de evaluación se ajustan con el mismo entrenamiento...
    assert first.n_train == second.n_train
    # ...así que el error en la prueba aumenta exactamente en la media del cambio.
    assert second.metrics.loc["modelo", "MAE"] == pytest.approx(50, abs=1e-6)
    assert second.metrics.loc["linea_base", "MAE"] > first.metrics.loc["linea_base", "MAE"]


def test_results_are_deterministic(sample_frame):
    first = fit_calendar_models(sample_frame, SPLIT)
    second = fit_calendar_models(sample_frame, SPLIT)
    for variable in TARGETS:
        pd.testing.assert_frame_equal(first[variable].metrics, second[variable].metrics)
        pd.testing.assert_series_equal(first[variable].hour_effects, second[variable].hour_effects)


def test_temperature_beats_its_baseline_on_the_samples(sample_frame):
    model = fit_calendar_model(sample_frame, "temperature_2m_c", SPLIT)
    assert model.metrics.loc["modelo", "MAE"] < model.metrics.loc["linea_base", "MAE"]
    assert model.n_all == model.n_train + model.n_test + 24


def test_parse_moment_formats():
    assert parse_moment("2026-11-03") == (
        datetime(2026, 11, 3, tzinfo=pd.Timestamp("2026-11-03", tz="America/Bogota").tzinfo),
        False,
    )
    assert parse_moment("2026-11-03 15")[0].hour == 15
    assert parse_moment("2026-11-03 15:00")[1] is True
    for bad in ("03/11/2026", "2026-02-30", "2026-11-03 24:00", "2026-11-03 15:30", "mañana"):
        with pytest.raises(PredictionRequestError):
            parse_moment(bad)


def local_hours(index: pd.DatetimeIndex) -> list[str]:
    return [f"{t:%Y-%m-%d %H:%M}" for t in index.tz_convert("America/Bogota")]


def test_date_only_yields_24_hours():
    hours = request_hours("2026-11-03", "", WIN, TODAY)
    assert len(hours) == 24
    assert local_hours(hours)[0] == "2026-11-03 00:00"
    assert local_hours(hours)[-1] == "2026-11-03 23:00"


def test_single_hour_and_ranges():
    assert local_hours(request_hours("2026-11-03 15:00", "", WIN, TODAY)) == ["2026-11-03 15:00"]
    assert len(request_hours("2026-11-03", "2026-11-05", WIN, TODAY)) == 72
    assert len(request_hours("2026-11-03 06", "2026-11-04 18:00", WIN, TODAY)) == 37


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2026-11-01", "2026-12-15", "máximo es 31 días"),
        ("2025-10-17", "", "desde el inicio"),
        ("2027-10-19", "", "un año después"),
        ("2026-11-05", "2026-11-03", "anterior"),
        ("ayer", "", "no es una fecha válida"),
    ],
)
def test_limits_are_explained(start, end, message):
    with pytest.raises(PredictionRequestError, match=message):
        request_hours(start, end, WIN, TODAY)


def test_last_allowed_day_and_31_days_are_accepted():
    assert len(request_hours("2027-10-18", "", WIN, TODAY)) == 24
    assert len(request_hours("2026-11-01", "2026-12-01 23:00", WIN, TODAY)) == 31 * 24


def test_prediction_table_with_and_without_real_values(sample_frame):
    models = fit_calendar_models(sample_frame, SPLIT)
    past = request_hours("2026-03-01", "", WIN, TODAY)
    table = predict(models, past, sample_frame)
    assert len(table) == 24
    assert str(table.index.tz) == "America/Bogota"
    temp = table["temperature_2m_c"]
    np.testing.assert_allclose(temp["diferencia"], temp["real"] - temp["prediccion"])
    assert temp["real"].notna().all()

    future = predict(models, request_hours("2027-01-15 15:00", "", WIN, TODAY), sample_frame)
    assert future[("temperature_2m_c", "real")].isna().all()
    assert future[("temperature_2m_c", "prediccion")].notna().all()
