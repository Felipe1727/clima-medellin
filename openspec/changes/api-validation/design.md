# Design

## Context

Las peticiones exploratorias del 2026-10-18 confirmaron: `models=era5` selecciona ERA5 (celda 6.25, -75.5); ERA5 publica hasta el día D−5 completo y devuelve los días posteriores como `null`; PM2.5 de `cams_global` llega con 24 valores por día y sin nulos en un año, con saltos medios grandes a las 00 y 12 UTC (empalme de las ejecuciones del pronóstico). La documentación de la Air Quality API no ofrece el parámetro `elevation` (solo aparece en la respuesta). El cliente HTTP definitivo llega en la especificación `ingest`; esta solo necesita descargar y guardar.

## Goals / Non-Goals

**Goals:**
- Muestras reproducibles y versionadas, con metadatos legibles por las pruebas.
- `docs/` coherente con las decisiones bloqueadas en el roadmap.

**Non-Goals:**
- Normalización, validación de rangos o el cliente con reintentos (especificación `ingest`).
- Gráfica de los empalmes (especificación `visualizations`); aquí solo se documenta su magnitud.

## Decisions

### Script autónomo con `requests`
- `python/scripts/fetch_samples.py` define las cuatro peticiones como datos (endpoint, parámetros, rango) a partir de la fecha D en America/Bogota y las ejecuta con `requests.get(..., timeout=60)`; ante un estado HTTP distinto de 200 termina con error.
- Guarda cada respuesta tal cual (JSON con sangría de 1 espacio para que los diffs sean legibles) y escribe `samples/manifest.json` (archivo, URL completa, parámetros, rango, fecha D y momento de descarga en UTC) y `samples/README.md` generado desde el mismo manifiesto.
- Alternativa descartada: reutilizar el cliente de `ingest`, que aún no existe; el script no forma parte del paquete de la aplicación.

### `elevation` solo en ERA5
- Se envía `elevation=1495` a la Historical Weather API, que lo usa para el reescalado estadístico. La Air Quality API no documenta ese parámetro, así que no se envía; se deja constancia en D-007.

### Pruebas guiadas por el manifiesto
- `python/tests/test_samples.py` lee `samples/manifest.json` para conocer la fecha D de la descarga y así comprobar los nulos finales de ERA5 desde las 00:00 UTC de D−4, sin depender de la fecha en que se ejecutan las pruebas.

### Magnitud de los empalmes
- Se calcula una vez sobre `cams_pm25_year.json` (salto absoluto medio hacia cada hora UTC) y se documenta en `fuentes-y-datos.md` con la fecha de la muestra.

### Actualización de la documentación
- Cada decisión del roadmap se refleja en su entrada de `decisiones.md` (estado final y texto de la decisión) y en la tabla de decisiones pendientes de `fases.md` (columna de resolución). Los PV-01…PV-12 se marcan como resueltos o justificados en `fases.md` y en `fuentes-y-datos.md`.

## Risks / Trade-offs

- [ERA5 se retrasa más de 5 días el día de la descarga] → la prueba de nulos finales fallaría; el script comprueba la condición tras descargar y avisa para repetir la descarga otro día.
- [Tamaño de las muestras en git] → cuatro archivos JSON de unos cientos de KB; aceptable y estable (se descargan una sola vez).
