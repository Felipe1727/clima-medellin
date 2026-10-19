# Proposal

## Why

Para guardar datos hay que pedirlos a Open-Meteo y convertir cada respuesta en una tabla limpia y validada antes de entregarla a Java (Fase 3). Sin esta pieza, el puente (`bridge`) y la actualización incremental (`coverage`) no tienen qué enviar.

## What Changes

- Configuración del proyecto en Python: ubicación `MED-CENTRO`, endpoints y parámetros fijados de cada fuente (ERA5 y CAMS global), zona horaria local.
- Cliente HTTP para las dos APIs: construye la petición con los parámetros fijados y un rango de fechas, y reintenta 3 veces con espera creciente ante tiempos de espera agotados, errores de conexión y respuestas 5xx.
- Normalización de una respuesta a un DataFrame de Pandas: índice UTC con zona horaria, columnas canónicas con la unidad en el nombre, comprobación de unidades, valores fuera de rango plausible convertidos en `null` y contados, duplicados eliminados, valores en o después del fin efectivo eliminados y filas con todas las variables a `null` descartadas, con un informe de lo que se hizo.
- El script de muestras reutiliza la configuración del paquete en lugar de repetirla.
- Documentación: sección 3 de `docs/implementacion.md`, rangos plausibles, Fase 3 en `docs/fases.md`, PV-16 y PV-17.

## Capabilities

### New Capabilities
- `data-ingestion`: descarga de las respuestas de Open-Meteo y su normalización a tablas horarias validadas, listas para guardarse.

### Modified Capabilities
<!-- Ninguna: api-samples no cambia de comportamiento (el script solo reutiliza la configuración). -->

## Impact

- Código nuevo: `python/src/clima_medellin/config.py`, `openmeteo.py`, `normalize.py`; pruebas en `python/tests/`.
- `python/scripts/fetch_samples.py` importa la configuración del paquete.
- Sin dependencias nuevas (requests y pandas ya están).
- Documentación: `docs/implementacion.md`, `docs/fuentes-y-datos.md`, `docs/fases.md`, `docs/cobertura-y-franjas.md`, `README.md`.
