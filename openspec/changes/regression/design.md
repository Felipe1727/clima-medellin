# Design

## Context

`dataset.combine` une las fuentes con un `outer join`; `split.temporal_split` define entrenamiento, hueco y prueba. La documentación del modelo está en `docs/regresion.md` (D-017 a D-020; DP-02 = todas las horas; DP-08 = escala original).

## Goals / Non-Goals

**Goals:**
- Una función pura `fit_and_evaluate(data, split)` que devuelva todo lo que la CLI y las gráficas necesitan.

**Non-Goals:**
- Gráficas de real frente a predicho y de residuos (especificación `visualizations`).
- Selección de variables, interacciones, transformación logarítmica o modelos no lineales (fuera del alcance).

## Decisions

### `regression.py`
- `PREDICTORS = ["temperature_2m_c", "relative_humidity_2m_pct", "wind_speed_10m_ms"]`, `TARGET = "pm25_ug_m3"`.
- `regression_dataset(frame) -> (data, excluded)`: `frame.dropna(subset=PREDICTORS + [TARGET])`; sobre la tabla de `combine` equivale a la unión interna con eliminación de nulos.
- `fit_and_evaluate(data, split) -> RegressionResult`:
  - `train = split.train(data)`, `test = split.test(data)`; si alguno está vacío, `ValueError` con un mensaje en español.
  - `Pipeline([("scaler", StandardScaler()), ("regression", LinearRegression())])` ajustado con `train`.
  - Coeficientes estandarizados = `regression.coef_`; en unidades originales = `coef_ / scaler.scale_`; intercepto original = `intercept_ − Σ coef_original · scaler.mean_`.
  - Métricas con `sklearn.metrics` (`mean_absolute_error`, `root_mean_squared_error`, `r2_score`); línea base = vector constante con la media de `y_train`.
  - VIF con `statsmodels.stats.outliers_influence.variance_inflation_factor` sobre las predictoras de entrenamiento con constante añadida (`statsmodels.tools.add_constant`), descartando la fila de la constante.
  - Durbin-Watson con `statsmodels.stats.stattools.durbin_watson` sobre los residuos de prueba en orden temporal.
- `RegressionResult`: `split`, `n_train`, `n_test`, `excluded` (opcional), `intercept_std`, `coefficients` (DataFrame con `estandarizado` y `original`), `intercept_original`, `baseline_value`, `metrics` (DataFrame filas `modelo`/`linea_base`, columnas `MAE`, `RMSE`, `R2`), `vif` (Series), `durbin_watson`, `predictions` (DataFrame de prueba con `real`, `predicho`, `residuo`).

### Por qué sin p-valores
Los residuos horarios están autocorrelacionados (se verá en Durbin-Watson): los errores estándar clásicos subestimarían la incertidumbre. `regresion.md` ya lo justifica; aquí simplemente no se calculan.

## Risks / Trade-offs

- [Pocas filas de prueba si hay huecos] → el resultado informa `n_train` y `n_test`; la CLI avisa si la cobertura no es COMPLETA.
- [VIF infinito con colinealidad perfecta] → `statsmodels` devuelve `inf`; se muestra tal cual.
