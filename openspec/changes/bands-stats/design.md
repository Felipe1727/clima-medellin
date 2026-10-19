# Design

## Context

`JavaBridge.export(source, start, end)` devuelve un DataFrame por fuente indexado por timestamp UTC (con `batch_id`). `coverage.window(today)` da la ventana. Las reglas de franjas y de perfil diurno están en `docs/cobertura-y-franjas.md`; la separación temporal en D-018.

## Goals / Non-Goals

**Goals:**
- Funciones puras sobre DataFrames, fáciles de comprobar a mano con un día de ejemplo.
- Una sola definición de la separación temporal, reutilizable por la regresión.

**Non-Goals:**
- Gráficas (especificación `visualizations`) y presentación en la terminal (especificación `cli-integration`).
- La regresión (especificación `regression`).

## Decisions

### `split.py`
- `add_months(day, months)`: suma meses naturales y recorta al último día del mes si el día no existe.
- `temporal_split(win) -> Split(train_start, train_end, test_start, test_end)` en UTC; `train_end` = 00:00 locales de `add_months(win.start_local, 9)`; `test_start = train_end + 24 h`; `test_end = win.end_utc`. `Split.train(frame)` / `Split.test(frame)` filtran con intervalos semiabiertos.

### `dataset.py`
- `combine(weather, air) -> DataFrame`: `outer join` por índice de las columnas canónicas (sin `batch_id`), ordenado.
- `load_window(bridge, win) -> DataFrame`: exporta las dos fuentes en [inicio, fin) de la ventana y las combina.

### `bands.py`
- `BANDS = {"mañana": (7, 8, 9), "tarde": (13, 14, 15), "noche": (19, 20, 21)}`, `MIN_VALID_HOURS = 2`.
- `to_local(frame)`: `tz_convert("America/Bogota")` (por nombre de zona, no con un desfase fijo).
- `daily_bands(frame) -> DataFrame` con índice = fecha civil local y columnas `MultiIndex (variable, franja)`: se filtran las horas locales de cada franja, se agrupa por `index.date` local y se calcula `mean` y `count`; `mean.where(count >= 2)`.
- `diurnal_profile(frame, split) -> DataFrame` con índice = hora local 0–23 y columnas `MultiIndex (variable, ["media", "n"])`, calculado solo con `split.train(frame)`; las horas sin datos aparecen con media NaN y n 0.

### `descriptive.py`
- `describe_variables(frame) -> DataFrame` (filas = variables; columnas `n, nulos, media, mediana, desv, min, max, p5, p25, p75, p95`). `nulos` cuenta los valores nulos de las filas presentes; las horas sin fila son responsabilidad de la cobertura. Percentiles con el método lineal de Pandas (`quantile`).
- `describe_bands(bands) -> DataFrame` (filas = (variable, franja); columnas `media`, `dias_validos`).

## Risks / Trade-offs

- [El perfil diurno con pocos datos de entrenamiento] → se muestra siempre `n` por hora, como pide la documentación.
- [`nulos` no incluye horas sin registro] → se documenta; la cobertura (opción 1) ya informa de los huecos.
