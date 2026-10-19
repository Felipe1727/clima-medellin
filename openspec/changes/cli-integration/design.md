# Design

## Context

Funciones disponibles: `coverage.window/today_local`, `update.current_coverage/plan_update/execute_plan`, `dataset.load_window`, `bands.daily_bands`, `descriptive.*`, `split.temporal_split`, `regression.*`, `plots.*` y `JavaBridge`. `cli.main` solo implementa `--version`.

## Goals / Non-Goals

**Goals:**
- Un menú que solo orquesta y formatea: ninguna regla de negocio nueva.
- Probable de extremo a extremo con entradas programadas, sin red y con una base temporal.

**Non-Goals:**
- Subcomandos no interactivos de la CLI de Python (el menú es la interfaz acordada).
- Guion de la defensa oral (fuera del alcance).

## Decisions

### `menu.py`: clase `Menu` con dependencias inyectables
- `Menu(bridge, *, fetch=openmeteo.fetch, today=None, outputs_dir=paths.OUTPUTS_DIR, input_fn=input, print_fn=print)`; `today=None` usa `coverage.today_local()` en cada acción.
- `run()`: bucle de cabecera + opciones; `7` termina; `EOFError`/`KeyboardInterrupt` terminan con despedida.
- Cada acción captura `BridgeError`, `OpenMeteoError`, `NormalizationError` y `ValueError` → `[ERROR] <mensaje>`.
- `_guard()` para las opciones 3–6: calcula la cobertura; si las dos fuentes están `SIN_DATOS` sugiere la opción 2; si alguna no es `COMPLETA`, `[AVISO]` y confirmación `[s/N]`.
- Opción 2: recorre el plan petición a petición llamando a `execute_plan` con un plan de una sola petición, para mostrar el progreso `[…] Descargando <fuente> <inicio> → <fin> (i/n)` y seguir si una falla. Llamadas equivalentes estimadas por petición = `ceil(días / 14)` (regla de Open-Meteo de 2 semanas por llamada con pocas variables).
- Opción 3: fuente (1 ERA5, 2 CAMS global), fechas `AAAA-MM-DD` locales inclusive → `[inicio 00:00 local, fin + 1 día 00:00 local)`; páginas de 20 filas (Enter = siguiente, `q` = terminar).
- Opción 6: modo (1 ventana, 2 PNG); genera 4 series, perfil, franjas, dispersión, correlación, 2 mapas de cobertura, empalmes, real frente a predicho y residuos (14 figuras).
- Tablas en texto con `DataFrame.to_string` y números redondeados; horas siempre en hora de Medellín y UTC al lado en la opción 3.

### `cli.py`
- `main(argv)`: argparse con `--version` y `--verbose`; construye `JavaBridge(verbose=...)` y ejecuta `Menu(...).run()`; devuelve 0.

### Pruebas
- `test_menu.py`: entradas programadas con un iterador y salida capturada en una lista; `JavaBridge` real con base temporal; `FakeOpenMeteo`; `outputs_dir` temporal; Matplotlib con Agg.
- Escenario de extremo a extremo: 1 → 2 (s) → 1 → 3 (ERA5, un día) → 4 → 5 → 6 (PNG) → 7.
- Escenarios cortos: opción inválida, base vacía en la opción 4, actualización cancelada, nada que descargar y error del puente (JAR inexistente).

## Risks / Trade-offs

- [Prueba de extremo a extremo lenta (varias JVM)] → un único escenario largo; el resto son cortos.
- [Pregunta de confirmación en 3–6 con cobertura PARCIAL] → en la prueba la API falsa deja las dos fuentes COMPLETA, así que no aparece; un escenario corto la cubre.
