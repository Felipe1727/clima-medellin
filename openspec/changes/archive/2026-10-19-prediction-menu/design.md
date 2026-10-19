# Design

## Context

`calendar_models` ofrece `fit_calendar_models`, `request_hours` y `predict`; `menu.py` (con `rich`) tiene la opción 6 como «próximamente»; `plots.py` tiene 9 gráficas.

## Goals / Non-Goals

**Goals:** usar los modelos de calendario desde el menú, comparar los cuatro modelos en la opción 5 y añadir las dos gráficas nuevas.

**Non-Goals:** cambios en los modelos o en sus límites.

## Decisions

- Opción 6: `guard()` como las demás; preguntas `Desde (ej. 2026-11-03 o 2026-11-03 15:00)` y `Hasta (Enter = solo esa fecha u hora; ej. 2026-11-05)`; un `PredictionRequestError` se muestra como `[ERROR]` sin salir del menú. Los modelos se ajustan con `fit_calendar_models(load_window(...), temporal_split(win))`.
- Hasta 48 horas (2 días): tabla hora a hora; columnas por variable `predicción` y, si alguna hora tiene dato, `real` y `diferencia`; fila final «error típico ±». Más de 48 horas: resumen diario (`media (mín–máx)` de la predicción por variable y la media real si existe), pregunta `[s/N]` para la tabla hora a hora (en páginas de 24) y pregunta de salida de la gráfica (1 ventana, 2 PNG; otra respuesta = sin gráfica).
- Panel «Qué significa»: valores típicos frente a pronóstico, error típico de cada variable y, con datos reales, la diferencia media observada.
- Opción 5: primera tabla con 4 filas (`modelo`, `unidad`, `error típico`, `error típico de la línea base`, `mejora (%)`, `R²`); los modelos de calendario usan la misma separación temporal que la regresión.
- `plots.hour_effects(models, start, end)` y `plots.prediction_chart(table, models)`: 3 paneles; colores de la paleta validada (predicción en color 1, real en color 2, banda en color 1 con transparencia).

## Risks / Trade-offs

- [Ajustar los tres modelos en cada predicción] → ~0,1 s; despreciable frente al arranque de la JVM de la exportación.
