# Proposal

## Why

Los modelos de calendario (`calendar-models`) ya existen, pero el usuario todavía no puede usarlos: la opción 6 dice «próximamente» y la opción 5 solo evalúa la regresión PM2.5 ← clima. Esta especificación cierra la segunda exploración (2026-10-19): pantalla de predicción, evaluación de los cuatro modelos y gráfica del efecto de cada hora.

## What Changes

- Opción 6: preguntas «Desde» y «Hasta» con los formatos y límites bloqueados; predicción de una hora, un día o un rango; las tres variables lado a lado con su error típico; valor real y diferencia en horas con datos guardados y «valor típico» en el resto; para rangos de más de 2 días, resumen diario, tabla hora a hora bajo petición y gráfica (ventana o PNG).
- Opción 5: tabla con los tres modelos de calendario y la regresión PM2.5 ← clima frente a su línea base, seguida del detalle de esta última y un panel «Qué significa».
- Opción 7: nueva gráfica «efecto de cada hora» (3 paneles); 14 gráficas en total.
- Gráfica de predicción para rangos (línea, banda de ± error típico y valores reales).
- Documentación: `cli-y-visualizaciones.md`, sección 12 de `implementacion.md`, README y Fase 10 completada.

## Capabilities

### New Capabilities
<!-- Ninguna. -->

### Modified Capabilities
- `interactive-menu`: la opción 6 predice; la opción 5 evalúa los cuatro modelos; la opción 7 genera 14 gráficas.
- `charts`: nuevas gráficas del efecto de cada hora y de la predicción de un rango.

## Impact

- Código: `menu.py`, `plots.py`; pruebas `test_menu.py` y `test_plots.py`.
- Documentación: `docs/cli-y-visualizaciones.md`, `docs/implementacion.md`, `docs/fases.md`, `README.md`.
