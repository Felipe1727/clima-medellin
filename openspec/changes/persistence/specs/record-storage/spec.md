# Spec Delta

## Purpose

Guarda en ObjectDB los registros horarios de meteorología y de calidad del aire con su procedencia, garantiza que cada (ubicación, fuente, timestamp) existe una sola vez y permite consultarlos por ubicación y rango.

## ADDED Requirements

### Requirement: Clave natural única en la base
La base SHALL impedir que existan dos registros de la misma entidad con la misma ubicación, fuente y timestamp UTC, aunque el código que inserta no lo compruebe.

#### Scenario: Inserción directa de un duplicado
- **WHEN** se intenta confirmar una transacción que persiste un registro cuya (ubicación, fuente, timestamp) ya existe
- **THEN** la confirmación falla y la base conserva un solo registro con esa clave

### Requirement: Inserción de un lote solo por adición
Guardar un lote SHALL crear un `IngestionBatch` con su fuente, ubicación, tipo `NORMAL`, rango pedido, momento de la ingesta, endpoint y parámetros, e insertar solo los registros cuya clave no existe. Cada registro insertado SHALL apuntar a su lote, y el lote SHALL guardar los conteos de recibidos, insertados, duplicados y rechazados. Ningún registro existente SHALL modificarse.

#### Scenario: Duplicado dentro del mismo lote
- **WHEN** un lote contiene dos filas con el mismo timestamp
- **THEN** se inserta una, la otra cuenta como duplicado y el resto del lote se inserta

#### Scenario: Duplicados de un lote anterior
- **WHEN** un segundo lote contiene timestamps ya guardados por un lote anterior y otros nuevos
- **THEN** solo se insertan los nuevos, los existentes cuentan como duplicados y conservan sus valores y su lote original

#### Scenario: Filas rechazadas
- **WHEN** un lote contiene una fila sin timestamp o con todas sus variables a `null`
- **THEN** esa fila no se guarda, cuenta como rechazada y el resto del lote se inserta

### Requirement: Confirmación en bloques
La inserción de un lote SHALL confirmar los registros en transacciones de como máximo 500 registros, de modo que un fallo en un bloque no deshaga los bloques ya confirmados.

#### Scenario: Lote grande
- **WHEN** se guarda un lote de 1 200 registros nuevos
- **THEN** se insertan los 1 200 en 3 bloques confirmados

### Requirement: Valores ausentes y timestamps exactos
Un valor ausente SHALL guardarse y recuperarse como `null`, nunca como 0, y un timestamp UTC SHALL recuperarse exactamente igual, sea cual sea la zona horaria de la JVM.

#### Scenario: Ida y vuelta de null
- **WHEN** se guarda un registro con el viento a `null` y se vuelve a leer
- **THEN** el viento leído es `null`

#### Scenario: Ida y vuelta del timestamp
- **WHEN** se guarda un registro con timestamp `2026-03-01T13:00:00Z` y se lee con la JVM en otra zona horaria
- **THEN** el timestamp leído es `2026-03-01T13:00:00Z`

### Requirement: Persistencia entre aperturas
Los datos SHALL conservarse al cerrar y volver a abrir el archivo de la base.

#### Scenario: Reapertura
- **WHEN** se guardan registros, se cierra la base y se vuelve a abrir
- **THEN** los conteos de registros y lotes son los mismos

### Requirement: Consulta por ubicación y rango
La capa de persistencia SHALL devolver los registros de una fuente para un código de ubicación y un rango UTC semiabierto [inicio, fin), ordenados por timestamp ascendente, y un resumen con el número de registros, el número de valores no nulos por variable y el primer y último timestamp.

#### Scenario: Consulta ordenada
- **WHEN** se guardan registros en desorden y se consultan por código y rango
- **THEN** se devuelven solo los del rango, ordenados por timestamp

#### Scenario: Resumen agregado
- **WHEN** se pide el resumen de una ubicación y fuente con registros que tienen algunos valores a `null`
- **THEN** el resumen cuenta los registros, los valores no nulos de cada variable y el primer y último timestamp

### Requirement: Ubicación única por código
Asegurar una ubicación SHALL crearla si su código no existe y devolver la existente si ya existe, sin duplicarla.

#### Scenario: Ubicación existente
- **WHEN** se asegura dos veces la ubicación `MED-CENTRO`
- **THEN** existe una sola ubicación con ese código
