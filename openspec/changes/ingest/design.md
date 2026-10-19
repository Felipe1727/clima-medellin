# Design

## Context

Las respuestas reales están en `samples/` (`api-validation`). Las dos APIs devuelven listas paralelas (`hourly.time` y una lista por variable) con horas GMT sin sufijo de zona (`2026-03-01T13:00`). ERA5 incluye como `null` los días aún no publicados. El paquete Python solo tiene el comando de humo; el script de muestras repite las constantes de la ubicación y de los parámetros.

## Goals / Non-Goals

**Goals:**
- Un cliente HTTP pequeño y probado sin red.
- Una normalización pura (sin E/S) que reciba el JSON ya decodificado y el fin efectivo, y devuelva la tabla y un informe.

**Non-Goals:**
- Cálculo de la ventana, del fin efectivo y de los intervalos faltantes (especificación `coverage`); aquí el fin efectivo es un parámetro.
- Escritura de JSON Lines y llamada al JAR (especificación `bridge`).

## Decisions

### `config.py`: una sola fuente de constantes
- `LOCATION` (código, nombre, latitud, longitud, elevación, zona horaria), `LOCAL_TZ = ZoneInfo("America/Bogota")`, y un `SourceConfig` por fuente (`ERA5`, `CAMS_GLOBAL`): URL, parámetros fijos, variables de la API y su columna canónica y unidad esperada. Los nombres de fuente coinciden con el enum `Source` de Java.
- `fetch_samples.py` importa estas constantes.

### `openmeteo.py`: cliente con reintentos explícitos
- `build_request(source, start, end) -> (url, params)`.
- `fetch(source, start, end, *, session=None, sleep=time.sleep) -> dict`: hasta 4 intentos (1 + 3 reintentos) con esperas de 1, 2 y 4 s; reintenta ante `requests.Timeout`, `requests.ConnectionError` y estados 5xx; un 4xx lanza `OpenMeteoError` de inmediato. `session` y `sleep` se inyectan para probar sin red ni esperas reales.
- Alternativa descartada: `urllib3.Retry` montado en un `HTTPAdapter`; es más opaco de explicar y de probar que un bucle de 15 líneas.

### `normalize.py`: transformación pura con informe
- `normalize(source, payload, effective_end) -> Normalized(frame, report)`.
- Pasos: (1) comprobar `hourly_units` contra las unidades esperadas; (2) `pd.to_datetime(times, utc=True)` como índice `timestamp_utc`; (3) renombrar columnas a las canónicas y convertir a `float` (los `None` pasan a `NaN`); (4) fuera de rango → `NaN` con `Series.where`, contando por columna; (5) eliminar duplicados del índice conservando el primero; (6) eliminar `timestamp >= effective_end`; (7) eliminar filas con todo `NaN`; (8) ordenar.
- `NormalizationReport`: `received`, `duplicates`, `after_effective_end`, `all_null`, `out_of_range` (dict por columna), `rows`.
- Los rangos plausibles viven en `config.py` junto a cada variable.

## Risks / Trade-offs

- [Open-Meteo cambia el formato] → la comprobación de unidades y de longitudes falla con un mensaje claro en lugar de guardar datos mal interpretados.
- [Rangos demasiado estrictos] → se eligieron amplios a propósito (solo detectan valores imposibles); los valores de la muestra anual están muy dentro (temperatura 15,5–30,4 °C, viento ≤ 3,1 m/s, PM2.5 ≤ 49,9 µg/m³).
