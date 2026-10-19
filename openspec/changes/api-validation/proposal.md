# Proposal

## Why

La Fase 1 del plan (validación de las APIs) se resolvió con peticiones reales durante la exploración del 2026-10-18, pero ni las respuestas de muestra ni los hallazgos están en el repositorio: `docs/` sigue mostrando como pendientes decisiones ya tomadas (D-006 y D-009 en revisión, DP-01…DP-12 abiertas). Además, las especificaciones siguientes necesitan respuestas reales guardadas para probar la ingesta sin red.

## What Changes

- Nuevo script `python/scripts/fetch_samples.py` que descarga, con los parámetros fijados en el roadmap, cuatro respuestas de Open-Meteo y las guarda en `samples/` junto con `samples/README.md` (URL, parámetros y fecha de descarga).
- Muestras versionadas: ERA5 de un año, ERA5 del último mes (con los nulos finales de los días aún no publicados), PM2.5 de un año y PM2.5 de la última semana.
- Pruebas sin red que verifican las propiedades de las muestras (paso horario en GMT, unidades, número de pasos, PM2.5 horario sin nulos, nulos finales de ERA5 después de D−5).
- Actualización de `docs/fuentes-y-datos.md` con los hallazgos de la Fase 1 y resolución de PV-01…PV-12.
- Actualización de `docs/decisiones.md`, `docs/fases.md` y `docs/cobertura-y-franjas.md` con las decisiones bloqueadas en el roadmap (D-005, D-006, D-007, D-009, D-013, D-018, D-022, D-023 y DP-01…DP-12).

## Capabilities

### New Capabilities
- `api-samples`: descarga reproducible y conjunto versionado de respuestas reales de Open-Meteo que sirven de referencia y de datos de prueba sin red.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código nuevo: `python/scripts/fetch_samples.py`, `python/tests/test_samples.py`.
- Datos nuevos versionados: `samples/*.json`, `samples/README.md` (del orden de 1 MB en total).
- Documentación: `docs/fuentes-y-datos.md`, `docs/decisiones.md`, `docs/fases.md`, `docs/cobertura-y-franjas.md`.
- El script es la única pieza que accede a la red; ninguna prueba lo hace.
