# Design

## Context

Decisiones bloqueadas en `openspec/roadmap.md` (segunda exploración). Ya existen `dataset.load_window`, `split.temporal_split` y `coverage.window`. La exploración midió (12 meses de entrenamiento, 11 trimestres): MAE ≈ 1,3 °C, 6 % y 4,6 µg/m³.

## Goals / Non-Goals

**Goals:** funciones puras sobre DataFrames que la CLI (`prediction-menu`) usará: rasgos, ajuste/evaluación/reajuste, peticiones y tabla.

**Non-Goals:** pantallas, gráficas y textos de la CLI (`cli-ux`, `prediction-menu`); guardar modelos.

## Decisions

- `calendar_models.py`:
  - `TARGETS = [temperatura, humedad, PM2.5]` (columnas canónicas).
  - `calendar_features(index) -> DataFrame`: convierte a America/Bogota; `h01`…`h23` (0/1, `float`) y `season_sin`, `season_cos`. Las columnas son siempre las mismas, aunque falte alguna hora en los datos.
  - `CalendarModel` (dataclass): `variable`, `final` (`LinearRegression` reajustado), `metrics` (filas `modelo`, `linea_base`; columnas `MAE`, `RMSE`, `R2`), `typical_error`, `hour_effects` (Serie 0–23, 0 en medianoche), `season_sin`, `season_cos`, `intercept`, `n_train`, `n_test`, `n_all`.
  - `fit_calendar_model(frame, variable, split)` y `fit_calendar_models(frame, split)`; sin escalador (coeficientes en unidades).
  - `parse_moment(text) -> (datetime local, tiene_hora)`; `request_hours(desde, hasta, win, today) -> DatetimeIndex` UTC; `PredictionRequestError(ValueError)`.
  - `predict(models, hours, actual=None) -> DataFrame`: índice = hora local; columnas `MultiIndex (variable, [prediccion, real, diferencia])`.
- Límite de 31 días: el número de horas pedidas no puede superar 31 × 24.
- Límite superior: la última hora pedida debe ser anterior a las 00:00 locales de hoy + 366 días (es decir, hasta el final del día hoy + 365).

## Risks / Trade-offs

- [Evaluación pesimista en humedad: 9 meses no cubren un año] → se documenta; las predicciones usan los 12 meses.
- [Un día con datos parciales] → la columna `real` queda nula donde no hay dato.
