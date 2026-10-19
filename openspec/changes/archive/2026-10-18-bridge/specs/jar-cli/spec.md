# Spec Delta

## ADDED Requirements

### Requirement: Opciones de los subcomandos
Los subcomandos SHALL recibir sus opciones como pares `--nombre valor`, SHALL aceptar `--db <ruta>` para elegir el archivo de la base (por defecto `data/clima.odb`) y SHALL responder con error `USAGE` (código 1) ante una opción desconocida, una opción sin valor, una opción obligatoria ausente o un valor inválido (por ejemplo, una fuente que no es `ERA5` ni `CAMS_GLOBAL`).

#### Scenario: Opción desconocida
- **WHEN** se ejecuta `import --db x.odb --foo 1`
- **THEN** stdout contiene un JSON con `error.type` igual a `USAGE` que menciona `--foo` y el código de salida es 1

#### Scenario: Fuente inválida
- **WHEN** se ejecuta `coverage --location MED-CENTRO --source OTRA --out c.jsonl`
- **THEN** el código de salida es 1 y el mensaje menciona la fuente

### Requirement: Formato JSON Lines
Los archivos de intercambio SHALL estar en UTF-8 con un objeto JSON por línea, timestamps ISO 8601 en UTC con sufijo `Z` en el campo `timestamp_utc`, los campos `location_code` y `source`, una sola fuente por archivo, las variables con la unidad en el nombre (`temperature_2m_c`, `relative_humidity_2m_pct`, `wind_speed_10m_ms`, `pm25_ug_m3`) y los ausentes como `null`.

#### Scenario: Línea de meteorología
- **WHEN** se exporta un registro de ERA5 con el viento ausente
- **THEN** su línea contiene `"timestamp_utc":"2026-03-01T13:00:00Z"`, `"source":"ERA5"`, `"location_code":"MED-CENTRO"` y `"wind_speed_10m_ms":null`

### Requirement: Subcomando import
`import --file <jsonl> --meta <json>` SHALL validar todas las líneas antes de escribir nada; si todas son válidas SHALL asegurar la ubicación descrita en los metadatos, guardar el lote con su procedencia (fuente, rango pedido, endpoint, parámetros) y responder `{"ok":true,"batch_id":...,"received":...,"inserted":...,"duplicates":...,"rejected":...}` con código 0.

#### Scenario: Importación correcta
- **WHEN** se importa un archivo válido de 24 líneas de ERA5 en una base vacía
- **THEN** la respuesta tiene `ok` a `true`, `received` 24 e `inserted` 24, y el código es 0

#### Scenario: Importación repetida
- **WHEN** se importa dos veces el mismo archivo
- **THEN** la segunda respuesta tiene `inserted` 0 y `duplicates` igual al número de líneas

#### Scenario: Línea corrupta
- **WHEN** el archivo tiene una línea que no es JSON válido, un timestamp inválido, un valor no numérico o una fuente distinta de la de los metadatos
- **THEN** la respuesta es un error `DATA` que indica el número de línea, el código es 2 y la base no cambia

#### Scenario: Archivo inexistente
- **WHEN** `--file` apunta a un archivo que no existe
- **THEN** la respuesta es un error `DATA` y el código es 2

### Requirement: Subcomando coverage
`coverage --location <código> --source <fuente> --out <jsonl>` SHALL escribir en `--out` una línea `{"timestamp_utc":...,"non_null":[...]}` por timestamp guardado, en orden, y SHALL responder con el número de registros, los valores no nulos por variable, el primer y el último timestamp, la ruta escrita y el número de líneas.

#### Scenario: Cobertura con nulos parciales
- **WHEN** hay 3 registros de ERA5 y uno tiene el viento a `null`
- **THEN** la respuesta tiene `count` 3 y `non_null.wind_speed_10m_ms` 2, y la línea de ese registro no incluye `wind_speed_10m_ms` en `non_null`

#### Scenario: Base vacía
- **WHEN** no hay registros de la fuente
- **THEN** la respuesta tiene `count` 0, `first` y `last` a `null` y el archivo queda vacío

### Requirement: Subcomando export
`export --location <código> --source <fuente> --from <ISO> --to <ISO> --out <jsonl>` SHALL escribir en `--out` los registros del rango [from, to) ordenados por tiempo, en el formato JSON Lines con el campo adicional `batch_id`, y SHALL responder con la ruta escrita y el número de líneas.

#### Scenario: Exportación de un rango
- **WHEN** se exporta un rango que contiene 10 de 24 registros guardados
- **THEN** el archivo tiene 10 líneas ordenadas y la respuesta indica `lines` 10

### Requirement: Errores de base de datos e inesperados
Si la base no se puede abrir (por ejemplo, porque otro proceso la tiene abierta) o falla una operación de persistencia, el JAR SHALL responder con un error `DATABASE` y código 3; cualquier otra excepción no prevista SHALL responder con un error `UNEXPECTED` y código 4. En ambos casos stdout SHALL seguir conteniendo un único objeto JSON.

#### Scenario: Ruta de base inválida
- **WHEN** `--db` apunta a un directorio existente
- **THEN** la respuesta es un error `DATABASE` y el código es 3
