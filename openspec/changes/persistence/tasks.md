# Tasks

## 1. Entidades

- [x] 1.1 Crear `Source`, `BatchType`, `Location`, `WeatherRecord`, `AirQualityRecord` e `IngestionBatch` en `co.climamedellin.entities` (comentarios en español, `@Unique` compuesto, tipos envoltorio, `Instant`) y verificar que `mvn -q -DskipTests package` compila

## 2. Servicio de persistencia

- [x] 2.1 Implementar `Database` y `RecordStore.ensureLocation`, con prueba JUnit de ubicación única por código, y verificar con `mvn -q verify`
- [x] 2.2 Implementar la inserción de lotes (precarga de claves, duplicados en el lote y entre lotes, rechazos, bloques de 500, reintento uno a uno, conteos en `IngestionBatch`) con pruebas de duplicados, rechazos, bloques de 1 200 registros y clave única en la base, y verificar con `mvn -q verify`
- [x] 2.3 Implementar las consultas por código y rango con `JOIN` y el resumen agregado, con pruebas de orden, rango, resumen, ida y vuelta de `null`, timestamp con otra zona horaria y reapertura, y verificar con `mvn -q verify`

## 3. Documentación

- [x] 3.1 Escribir la sección 2 de `docs/implementacion.md` (EntityManagerFactory, anotaciones, `@Unique`, transacciones, `persist`, consulta JPQL, `JOIN`, agregaciones, `null`) con fragmentos reales, y verificar que `uv run pytest` (prueba de fragmentos) pasa
- [x] 3.2 Actualizar `docs/arquitectura.md` (PV-13, PV-14, entidades definitivas, registros de ObjectDB), `docs/decisiones.md` (D-010, D-011) y `docs/fases.md` (Fase 2 completada, PV-13 y PV-14 resueltos); verificar que no quedan `[Por verificar, Fase 2]`
- [x] 3.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `persistence` como hecho en `openspec/roadmap.md`.
