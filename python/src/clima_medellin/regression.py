"""Regresión lineal de PM2.5 frente a temperatura, humedad y viento (D-017 a D-020)."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tools import add_constant

from clima_medellin.split import Split

PREDICTORS = ["temperature_2m_c", "relative_humidity_2m_pct", "wind_speed_10m_ms"]
TARGET = "pm25_ug_m3"


def regression_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Solo las horas con PM2.5 y las tres predictoras; devuelve también las excluidas.

    Sobre la tabla de ``dataset.combine`` (unión externa) equivale a una unión interna
    seguida de quitar las filas con algún nulo. No se imputa nada.
    """
    data = frame.dropna(subset=PREDICTORS + [TARGET])[PREDICTORS + [TARGET]]
    return data, len(frame) - len(data)


@dataclass
class RegressionResult:
    split: Split
    n_train: int
    n_test: int
    coefficients: pd.DataFrame
    intercept_std: float
    intercept_original: float
    baseline_value: float
    metrics: pd.DataFrame
    vif: pd.Series
    durbin_watson: float
    predictions: pd.DataFrame
    pipeline: Pipeline


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": root_mean_squared_error(y_true, y_pred),
        "R2": r2_score(y_true, y_pred),
    }


def fit_and_evaluate(data: pd.DataFrame, split: Split) -> RegressionResult:
    """Ajusta con el entrenamiento y evalúa con la prueba, frente a la línea base."""
    train, test = split.train(data), split.test(data)
    if train.empty or test.empty:
        raise ValueError(
            "No hay datos suficientes: el entrenamiento o la prueba quedaron vacíos "
            f"({len(train)} y {len(test)} filas)."
        )
    x_train, y_train = train[PREDICTORS], train[TARGET]
    x_test, y_test = test[PREDICTORS], test[TARGET]

    # El escalador aprende media y desviación solo del entrenamiento (D-019).
    pipeline = Pipeline([("scaler", StandardScaler()), ("regression", LinearRegression())])
    pipeline.fit(x_train, y_train)
    predicted = pipeline.predict(x_test)

    # Línea base: la media del PM2.5 de entrenamiento, sin mirar ninguna predictora (D-020).
    baseline_value = float(y_train.mean())
    baseline = np.full(len(y_test), baseline_value)
    metrics = pd.DataFrame(
        {"modelo": _metrics(y_test, predicted), "linea_base": _metrics(y_test, baseline)}
    ).T

    scaler = pipeline.named_steps["scaler"]
    model = pipeline.named_steps["regression"]
    original = model.coef_ / scaler.scale_
    coefficients = pd.DataFrame(
        {"estandarizado": model.coef_, "original": original}, index=PREDICTORS
    )
    intercept_original = float(model.intercept_ - np.sum(original * scaler.mean_))

    # VIF con las predictoras de entrenamiento; la columna 0 es la constante añadida.
    with_constant = add_constant(x_train.to_numpy())
    vif = pd.Series(
        [variance_inflation_factor(with_constant, i + 1) for i in range(len(PREDICTORS))],
        index=PREDICTORS,
    )

    residuals = y_test.to_numpy() - predicted
    predictions = pd.DataFrame(
        {"real": y_test.to_numpy(), "predicho": predicted, "residuo": residuals},
        index=test.index,
    )
    return RegressionResult(
        split=split,
        n_train=len(train),
        n_test=len(test),
        coefficients=coefficients,
        intercept_std=float(model.intercept_),
        intercept_original=intercept_original,
        baseline_value=baseline_value,
        metrics=metrics,
        vif=vif,
        durbin_watson=float(durbin_watson(residuals)),
        predictions=predictions,
        pipeline=pipeline,
    )
