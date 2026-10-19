# Proposal

## Why

El JAR todavía no guarda nada. Antes de construir el puente con Python (`bridge`) hace falta la capa de persistencia: las cuatro entidades de [arquitectura.md](../../../docs/arquitectura.md#modelo-de-clases), la clave natural que impide duplicados en la base (D-011), la inserción solo por adición en bloques (D-013) y las consultas que después usarán `coverage` y `export`.

## What Changes

- Entidades JPA `Location`, `WeatherRecord`, `AirQualityRecord` e `IngestionBatch`, con tipos envoltorio que admiten `null` (D-012), unidades en el nombre de los campos (D-022) y `java.time.Instant` para los timestamps UTC.
- Índice único compuesto (ubicación, fuente, timestamp UTC) en cada entidad de registros.
- Servicio de persistencia que abre la base en una ruta dada, crea la ubicación si no existe y guarda un lote: crea el `IngestionBatch`, precarga las claves existentes del rango, omite y cuenta duplicados (también dentro del mismo lote), rechaza filas sin timestamp o con todas las variables a `null` y confirma en bloques de 500.
- Consultas JPQL: registros por código de ubicación y rango con `JOIN` sobre `Location`, ordenados por tiempo, y resumen agregado (conteos por variable, primer y último timestamp).
- Pruebas JUnit sobre una base temporal.
- Documentación: sección 2 de `docs/implementacion.md` (ObjectDB) y resolución de PV-13 y PV-14 en `docs/arquitectura.md`; Fase 2 en `docs/fases.md`; D-010 y D-011 confirmadas.

## Capabilities

### New Capabilities
- `record-storage`: almacenamiento persistente de registros meteorológicos y de calidad del aire con su procedencia, sin duplicados y solo por adición, y su consulta por ubicación y rango.

### Modified Capabilities
<!-- Ninguna: los subcomandos del JAR (capacidad jar-cli) llegan en la especificación bridge. -->

## Impact

- Código nuevo en `java/src/main/java/co/climamedellin/entities/` y `.../persistence/`, con pruebas en `java/src/test/java/`.
- Sin dependencias nuevas: la anotación `@Unique` (`javax.jdo.annotations.Unique`) viene incluida en el JAR de ObjectDB.
- Documentación: `docs/implementacion.md`, `docs/arquitectura.md`, `docs/fases.md`, `docs/decisiones.md`.
