# Proposal

## Why

Python y Java ya tienen cada uno su parte (ingesta y normalización; persistencia en ObjectDB), pero todavía no se hablan. Esta especificación implementa el protocolo de [arquitectura.md](../../../docs/arquitectura.md#protocolo-de-comunicación) (Fase 4): los subcomandos del JAR y el módulo de Python que los invoca, con un formato JSON Lines común y códigos de salida que Python traduce a mensajes en español.

## What Changes

- Subcomandos del JAR:
  - `import`: lee un archivo JSON Lines de `staging/` y los metadatos del lote (`--meta`, JSON), valida todas las líneas antes de escribir, asegura la ubicación y guarda el lote con `RecordStore`.
  - `coverage`: devuelve por stdout el resumen (conteos por variable, primer y último timestamp) y escribe en `exchange/coverage-<fuente>.jsonl` una línea por timestamp guardado con sus variables no nulas.
  - `export`: escribe en `exchange/export-<fuente>.jsonl` los registros de una ubicación, fuente y rango, con el lote de origen.
  - Opción común `--db <ruta>`; errores con el sobre JSON y los códigos 1 (uso), 2 (datos), 3 (base de datos) y 4 (inesperado).
- Módulo Python `bridge`: ejecuta el JAR como proceso hijo, interpreta el único JSON de stdout, traduce los códigos de salida a mensajes en español, escribe y borra los lotes de `staging/` según la política acordada, lee las exportaciones de `exchange/` y muestra el stderr de Java solo en modo detallado.
- Módulo Python de JSON Lines (DataFrame ↔ archivo) y rutas del proyecto.
- Documentación: sección 4 de `docs/implementacion.md`; DP-05, PV-15 y PV-19 resueltos en `docs/arquitectura.md`; Fase 4 en `docs/fases.md`.

## Capabilities

### New Capabilities
- `persistence-bridge`: comunicación de Python con el JAR de persistencia (lotes en JSON Lines, interpretación de respuestas y errores, ciclo de vida de los archivos intermedios).

### Modified Capabilities
- `jar-cli`: se añaden los subcomandos `import`, `coverage` y `export`, la opción `--db` y los códigos de salida de datos, base de datos e inesperado.

## Impact

- Java: `co.climamedellin.cli` (opciones, subcomandos, JSON Lines); `Main` despacha los subcomandos.
- Python: `clima_medellin/paths.py`, `jsonlines.py`, `bridge.py`; pruebas que ejecutan el JAR real contra una base temporal.
- Documentación: `docs/implementacion.md`, `docs/arquitectura.md`, `docs/fases.md`, `docs/decisiones.md`.
