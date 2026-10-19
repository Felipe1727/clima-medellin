# Tasks

## 1. Muestras de las APIs

- [x] 1.1 Implementar `python/scripts/fetch_samples.py` (peticiones como datos a partir de D en America/Bogota, descarga, `manifest.json` y `README.md` generados, comprobación de nulos finales) y verificar con `uv run ruff check .`
- [x] 1.2 Ejecutar el script y verificar que `samples/` contiene los cuatro JSON, `manifest.json` y `README.md` con URL, parámetros y fecha
- [x] 1.3 Escribir `python/tests/test_samples.py` (paso horario GMT, unidades, 8 760/8 784 pasos, PM2.5 24 valores/día sin nulos, nulos finales de ERA5 desde D−4 según el manifiesto) y verificar que `uv run pytest` pasa

## 2. Documentación de la Fase 1

- [x] 2.1 Calcular la magnitud de los empalmes de PM2.5 sobre la muestra anual y actualizar `docs/fuentes-y-datos.md` (hallazgos de la Fase 1, línea de ERA5T, atribución de CAMS global, PV-01…PV-12 resueltos o justificados); verificar que no quedan `[Por verificar, Fase 1]` sin resolver
- [x] 2.2 Actualizar `docs/decisiones.md` (D-005, D-006, D-007, D-009, D-013, D-018, D-022, D-023 con el texto y estado finales) y verificar que D-006 y D-009 ya no están en "pendiente de revisión"
- [x] 2.3 Actualizar `docs/fases.md` (Fase 1 completada, DP-01…DP-12 resueltas, PV-01…PV-12 resueltos) y `docs/cobertura-y-franjas.md` (PM2.5 horario, misma regla de franjas, aviso de empalmes, regla de DP-12, ventana efectiva de ERA5); verificar que las tablas reflejan las decisiones del roadmap
- [x] 2.4 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `api-validation` como hecho en `openspec/roadmap.md`.
