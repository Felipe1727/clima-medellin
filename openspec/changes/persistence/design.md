# Design

## Context

El JAR solo tiene el punto de entrada (`project-scaffold`). Un experimento previo con ObjectDB 2.9.5 (`objectdb-jk`) en este equipo mostró:

- `@javax.jdo.annotations.Unique(members = {"location", "source", "timestampUtc"})` funciona con el campo de relación `location`: un duplicado hace fallar la confirmación con `RollbackException` (PV-13).
- `java.time.Instant` se guarda y se recupera exacto aunque la JVM que lee tenga otra zona horaria (UTC, America/Bogota, Asia/Tokyo) (PV-14).
- ObjectDB escribe sus registros internos en un directorio `log/` junto al JAR que lo contiene (`java/target/log/` para el JAR del proyecto, ignorado por git) y, con Java 25, imprime en stderr un aviso sobre `sun.misc.Unsafe` (stdout queda limpio).

## Goals / Non-Goals

**Goals:**
- Entidades y servicio de persistencia listos para que `bridge` los exponga como subcomandos.
- Deduplicación en la base, inserción robusta por bloques y consultas que no carguen más de lo necesario.

**Non-Goals:**
- Subcomandos `coverage`, `import`, `export`, JSON Lines y códigos de salida (especificación `bridge`).
- Lotes de corrección (fuera del alcance, DP-04).

## Decisions

### Entidades (`co.climamedellin.entities`)
- `Location`: `id` generado, `code` con `@Unique`, `name`, `latitude`, `longitude`, `elevationM`, `timezone`.
- `WeatherRecord`: `id`, `location` (`@ManyToOne`), `source` (`Source`, `@Enumerated(STRING)`), `timestampUtc` (`Instant`), `temperature2mC`, `relativeHumidity2mPct`, `windSpeed10mMs` (`Double`), `batch` (`@ManyToOne IngestionBatch`). `@Unique(members = {"location", "source", "timestampUtc"})`.
- `AirQualityRecord`: igual con `pm25UgM3`.
- `IngestionBatch`: `id`, `batchId` (UUID en texto, `@Unique`), `source`, `location`, `type` (`BatchType`, solo `NORMAL`), `requestedStartUtc`, `requestedEndUtc`, `ingestedAtUtc` (`Instant`), `endpoint`, `params` (texto JSON), `received`, `inserted`, `duplicates`, `rejected` (`int`), `notes`.
- `Source` (`ERA5`, `CAMS_GLOBAL`) y `BatchType` (`NORMAL`) son enums, no entidades: no consumen clases del límite gratuito (4 de 10).
- Sin superclase común para los registros: se repiten tres campos, pero cada clase es autocontenida y su índice único es explícito. Alternativa descartada: `@MappedSuperclass`, que añade una clase más y oculta en otra clase los miembros del índice.
- Constructor sin argumentos `protected` (lo exige JPA) y campos privados con getters.

### Servicio (`co.climamedellin.persistence`)
- `Database implements AutoCloseable`: abre `EntityManagerFactory` con `objectdb:<ruta>` (crea el archivo si no existe; crea antes el directorio padre).
- `RecordStore` (recibe la `Database`):
  - `ensureLocation(LocationData)`: busca por código; si no existe la persiste.
  - `insertWeather(Location, BatchInfo, List<WeatherValues>)` e `insertAirQuality(...)` delegan en un método genérico privado. Los DTO de entrada son `record` de Java (`WeatherValues(Instant timestampUtc, Double temperature2mC, ...)`).
  - Algoritmo: (1) persistir el `IngestionBatch` con conteos a 0 y confirmar; (2) rechazar filas sin timestamp o con todas las variables a `null`; (3) cargar con una consulta JPQL los timestamps existentes de (ubicación, fuente) entre el mínimo y el máximo del lote; (4) recorrer las filas: si el timestamp está en el conjunto de existentes o ya apareció en el lote, cuenta como duplicado; si no, se añade al bloque; (5) confirmar cada 500 registros con `em.clear()` tras cada bloque para no acumular objetos en memoria; (6) si la confirmación de un bloque falla, se reintentan sus registros uno a uno y los que vuelvan a fallar cuentan como rechazados; (7) actualizar los conteos del lote y confirmar.
  - Devuelve `InsertResult(batchId, received, inserted, duplicates, rejected, blocksCommitted)`.
  - `findWeather(code, from, to)` / `findAirQuality(...)`: `SELECT r FROM WeatherRecord r JOIN r.location l WHERE l.code = :code AND r.timestampUtc >= :from AND r.timestampUtc < :to ORDER BY r.timestampUtc`.
  - `summarizeWeather(code)` / `summarizeAirQuality(code)`: una consulta agregada `COUNT(r)`, `COUNT(r.campo)` por variable, `MIN`/`MAX` del timestamp → `RecordSummary(count, nonNullByVariable, first, last)`.
- La regla de la Fase 1 «nunca filas con todo a `null`» (DP-12) la aplica Python, y Java la vuelve a aplicar como rechazo defensivo.

### Pruebas
- JUnit 5 con `@TempDir`: cada prueba abre una base nueva. La prueba de timestamps cambia `TimeZone.setDefault` a America/Bogota al leer y la restaura al final.

## Risks / Trade-offs

- [Consulta de claves existentes con lotes muy grandes] → un año son ~8 760 timestamps; un `Set<Instant>` de ese tamaño es trivial.
- [Directorio `log/` de ObjectDB al ejecutar las pruebas desde Maven] → se crea junto al JAR de ObjectDB en `~/.m2`, fuera del repositorio; para el JAR del proyecto queda en `java/target/log/`, ignorado.
- [Aviso de `sun.misc.Unsafe` en stderr] → no afecta al contrato (stdout limpio); `bridge` puede lanzar la JVM con `--sun-misc-unsafe-memory-access=allow` para silenciarlo.
