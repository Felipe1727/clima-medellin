"""Pruebas de la regresión con datos sintéticos de coeficientes conocidos."""

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from clima_medellin.regression import PREDICTORS, TARGET, fit_and_evaluate, regression_dataset
from clima_medellin.split import Split

SPLIT = Split(
    train_start=datetime(2026, 1, 1, tzinfo=UTC),
    train_end=datetime(2026, 1, 31, tzinfo=UTC),
    test_start=datetime(2026, 2, 1, tzinfo=UTC),
    test_end=datetime(2026, 2, 11, tzinfo=UTC),
)


def synthetic(seed: int = 0, collinear: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = pd.date_range(SPLIT.train_start, SPLIT.test_end, freq="h", tz="UTC", inclusive="left")
    n = len(index)
    t = rng.normal(21, 3, n)
    rh = 140 - 3 * t + rng.normal(0, 0.05, n) if collinear else rng.normal(80, 10, n)
    w = rng.gamma(2, 0.5, n)
    pm = 5 + 2 * t - 0.1 * rh - 3 * w + rng.normal(0, 0.01, n)
    return pd.DataFrame(
        {PREDICTORS[0]: t, PREDICTORS[1]: rh, PREDICTORS[2]: w, TARGET: pm}, index=index
    )


def test_incomplete_rows_are_excluded():
    frame = synthetic().iloc[:10].copy()
    frame.iloc[[0, 1], :3] = np.nan  # sin meteorología
    frame.iloc[5, 2] = np.nan  # viento nulo
    data, excluded = regression_dataset(frame)
    assert len(data) == 7 and excluded == 3
    assert list(data.columns) == PREDICTORS + [TARGET]


def test_known_coefficients_are_recovered():
    result = fit_and_evaluate(synthetic(), SPLIT)
    original = result.coefficients["original"]
    assert original[PREDICTORS[0]] == pytest.approx(2, abs=1e-2)
    assert original[PREDICTORS[1]] == pytest.approx(-0.1, abs=1e-3)
    assert original[PREDICTORS[2]] == pytest.approx(-3, abs=1e-2)
    assert result.intercept_original == pytest.approx(5, abs=0.05)
    assert result.metrics.loc["modelo", "R2"] > 0.999
    assert result.metrics.loc["modelo", "MAE"] < result.metrics.loc["linea_base", "MAE"]


def test_scaler_is_fitted_with_training_rows_only():
    data = synthetic()
    result = fit_and_evaluate(data, SPLIT)
    scaler = result.pipeline.named_steps["scaler"]
    np.testing.assert_allclose(scaler.mean_, SPLIT.train(data)[PREDICTORS].mean().to_numpy())
    # Con la media de todo el periodo sería distinta.
    assert not np.allclose(scaler.mean_, data[PREDICTORS].mean().to_numpy())


def test_split_and_gap_are_respected():
    data = synthetic()
    result = fit_and_evaluate(data, SPLIT)
    train_rows = SPLIT.train(data)
    assert result.n_train == len(train_rows)
    assert train_rows.index.max() < pd.Timestamp(SPLIT.train_end)
    assert result.predictions.index.min() >= pd.Timestamp(SPLIT.train_end) + pd.Timedelta(hours=24)
    gap = data[(data.index >= SPLIT.train_end) & (data.index < SPLIT.test_start)]
    assert result.n_train + result.n_test + len(gap) == len(data)


def test_baseline_uses_the_training_mean():
    data = synthetic()
    result = fit_and_evaluate(data, SPLIT)
    train_mean = SPLIT.train(data)[TARGET].mean()
    assert result.baseline_value == pytest.approx(train_mean)
    y_test = SPLIT.test(data)[TARGET]
    assert result.metrics.loc["linea_base", "MAE"] == pytest.approx(
        (y_test - train_mean).abs().mean()
    )


def test_collinear_predictors_have_high_vif():
    result = fit_and_evaluate(synthetic(collinear=True), SPLIT)
    assert result.vif[PREDICTORS[0]] > 10 and result.vif[PREDICTORS[1]] > 10
    independent = fit_and_evaluate(synthetic(), SPLIT)
    assert (independent.vif < 1.1).all()


def test_durbin_watson_and_predictions():
    result = fit_and_evaluate(synthetic(), SPLIT)
    assert 1.5 < result.durbin_watson < 2.5  # residuos de ruido blanco
    assert list(result.predictions.columns) == ["real", "predicho", "residuo"]
    assert len(result.predictions) == result.n_test


def test_results_are_reproducible():
    first, second = fit_and_evaluate(synthetic(), SPLIT), fit_and_evaluate(synthetic(), SPLIT)
    pd.testing.assert_frame_equal(first.coefficients, second.coefficients)
    pd.testing.assert_frame_equal(first.metrics, second.metrics)


def test_empty_period_raises_a_clear_error():
    data = SPLIT.train(synthetic())
    with pytest.raises(ValueError, match="prueba quedaron vacíos"):
        fit_and_evaluate(data, SPLIT)
