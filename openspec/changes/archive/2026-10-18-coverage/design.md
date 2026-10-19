# Design

## Context

`JavaBridge.coverage(source)` devuelve los timestamps guardados con sus variables no nulas; `openmeteo.fetch` y `normalize` descargan y limpian; `JavaBridge.import_frame` guarda. Como nunca se guardan filas con todo a `null` (DP-12), «tiene registro» equivale a «tiene al menos un valor». Las muestras versionadas cubren de 2025-10-18T00Z a 2026-10-17T23Z, mientras que la ventana de cualquier fecha D va de las 05:00 UTC de D−1 año a las 05:00 UTC de D, así que ninguna ventana cabe entera en las muestras.

## Goals / Non-Goals

**Goals:**
- Toda la aritmética de cobertura en funciones puras, probadas sin red ni JAR.
- Un flujo de actualización separable en «plan» y «ejecución», para que la CLI muestre el plan y pida confirmación antes de descargar.

**Non-Goals:**
- El menú, los mensajes y la confirmación interactiva (especificación `cli-integration`).
- La gráfica del mapa de cobertura (especificación `visualizations`).

## Decisions

### `coverage.py` (puro)
- `one_year_before(day)`, `window(today_local) -> Window(start_local, end_local, start_utc, end_utc, days)`.
- `effective_end(source, window, today_local)`.
- `expected_steps(start, end) -> DatetimeIndex` horario, `missing_steps(expected, existing_index)`.
- `group_intervals(index) -> list[(primero, último)]` de horas consecutivas; `to_request_dates(intervals) -> list[(date, date)]` en fechas UTC, fusionando rangos que se tocan (el siguiente empieza como mucho un día después del final del anterior).
- `variable_coverage(expected, valid_index) -> VariableCoverage(column, expected, valid, percent, max_gap_hours, gaps)`; los huecos son los grupos de `missing_steps(expected, valid)`.
- `coverage_report(source, snapshot_existing, window, eff_end) -> CoverageReport(source, start_utc, effective_end, records_in_window, variables, state)`; constantes `MIN_COVERAGE_PCT = 98.0`, `MAX_GAP_HOURS = 6`.
- `today_local()` usa `datetime.now(LOCAL_TZ).date()`; todas las demás funciones reciben la fecha como parámetro para poder probarlas con fechas fijas.

### `update.py`
- `plan_update(bridge, today) -> UpdatePlan(window, requests: list[PlannedRequest(source, start_date, end_date)])`.
- `execute_plan(bridge, plan, today, *, fetch=openmeteo.fetch) -> list[RequestResult(request, normalization_report, outside_window, import_response)]`: por cada petición descarga, normaliza con el fin efectivo, descarta lo anterior al inicio de la ventana (las fechas UTC del primer día empiezan a las 00:00, cinco horas antes de la ventana) e importa con `import_frame` (también si la tabla queda vacía).
- `update(bridge, today, *, fetch) -> UpdateOutcome(plan, results, coverage)` encadena plan, ejecución y una nueva cobertura de cada fuente.
- `fetch` se inyecta: las pruebas pasan una función falsa.

### Capa HTTP falsa para las pruebas de integración
- Construye para cualquier rango de fechas pedido una respuesta con el formato real de Open-Meteo, tomando cada valor de la muestra anual por (mes, día, hora) de la misma fecha de calendario; así puede servir cualquier ventana con valores reales de las muestras.
- Imita la latencia de ERA5: horas desde las 00:00 UTC de D−4 → `null`.
- Opciones para omitir un día (devolverlo con nulos) o devolver una respuesta vacía.

## Risks / Trade-offs

- [Pruebas de integración lentas] → cada llamada al JAR arranca una JVM (~1 s); se limitan a 3–4 escenarios.
- [Petición del primer día que empieza antes de la ventana] → se descargan hasta 5 horas de más y se descartan antes de guardar; se informa como `outside_window`.
