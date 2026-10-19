# Tasks

## 1. Configuración y cliente HTTP

- [x] 1.1 Crear `clima_medellin/config.py` (ubicación, zona horaria, configuración por fuente con variables, columnas, unidades y rangos) y hacer que `scripts/fetch_samples.py` la importe; verificar con `uv run ruff check .` y `uv run pytest` (pruebas de muestras)
- [x] 1.2 Implementar `clima_medellin/openmeteo.py` (`build_request`, `fetch` con 3 reintentos y esperas crecientes, `OpenMeteoError`) con pruebas de parámetros por fuente, reintento tras 503, reintentos agotados por timeout y 4xx sin reintento usando una sesión falsa; verificar con `uv run pytest`

## 2. Normalización

- [x] 2.1 Implementar `clima_medellin/normalize.py` (unidades, índice UTC, columnas canónicas, rangos, duplicados, fin efectivo, filas vacías, informe) con pruebas sobre las muestras: 8 664 filas de ERA5, 8 760 de PM2.5, sin duplicados, nulos parciales conservados, valor de 80 °C detectado, nulos finales eliminados, fila vacía intermedia descartada, timestamp repetido, unidad inesperada y America/Bogota = UTC−5 todo el año (PV-16); verificar con `uv run pytest`

## 3. Documentación

- [x] 3.1 Escribir la sección 3 de `docs/implementacion.md` (petición HTTP con requests, reintentos, JSON → DataFrame, UTC, validación con `where`, NaN frente a 0) con fragmentos reales; verificar con `uv run pytest`
- [x] 3.2 Documentar los rangos plausibles en `docs/fuentes-y-datos.md`, marcar la Fase 3 en `docs/fases.md` (PV-16 y PV-17 resueltos), actualizar la nota de PV-16 en `docs/cobertura-y-franjas.md` y `docs/decisiones.md` (D-008) y los requisitos con versiones reales en `README.md`; verificar que no quedan `[Por verificar, Fase 3]`
- [ ] 3.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `ingest` como hecho en `openspec/roadmap.md`.
