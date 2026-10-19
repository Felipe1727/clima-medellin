# persistence-bridge Specification

## Purpose
Conecta la aplicación Python con el JAR de persistencia: entrega lotes en JSON Lines, interpreta las respuestas y los errores del JAR y gestiona los archivos intermedios de `staging/` y `exchange/`.

## Requirements

### Requirement: Ida y vuelta sin pérdida
Un DataFrame normalizado importado mediante el puente y después exportado SHALL volver con los mismos timestamps UTC, los mismos valores y los mismos nulos.

#### Scenario: Ida y vuelta de ERA5
- **WHEN** se importa la tabla normalizada de una muestra de ERA5 con algún valor nulo y se exporta el mismo rango
- **THEN** la tabla exportada es idéntica en índice, columnas, valores y nulos

### Requirement: Interpretación de la respuesta del JAR
El puente SHALL interpretar como respuesta el único objeto JSON de stdout. Si el código de salida no es 0 SHALL fallar con un mensaje en español según el código (1 uso, 2 datos, 3 base de datos, 4 inesperado) que incluya el mensaje de Java; si stdout no es un único objeto JSON SHALL fallar indicando que la respuesta no es válida.

#### Scenario: Lote con una línea corrupta
- **WHEN** el JAR responde con código 2
- **THEN** el puente falla con un mensaje en español que indica que el lote tiene datos inválidos e incluye el número de línea

#### Scenario: Base en uso
- **WHEN** el JAR responde con código 3
- **THEN** el mensaje en español indica que no se pudo usar la base y sugiere cerrar otras ejecuciones

### Requirement: Ciclo de vida de los archivos intermedios
El puente SHALL escribir cada lote en un archivo nuevo de `staging/`, SHALL borrarlo tras una importación correcta y SHALL conservarlo, indicando su ruta en el error, si la importación falla. Cada exportación y cada consulta de cobertura SHALL sobrescribir un archivo de nombre fijo por fuente en `exchange/`. Ninguna operación del puente SHALL borrar el contenido de `exchange/`.

#### Scenario: Importación correcta
- **WHEN** una importación termina con código 0
- **THEN** el archivo de `staging/` del lote ya no existe

#### Scenario: Importación fallida
- **WHEN** una importación termina con un código distinto de 0
- **THEN** el archivo de `staging/` sigue existiendo y su ruta aparece en el error

### Requirement: Registros de Java solo en modo detallado
El stderr de Java SHALL ocultarse por defecto y SHALL mostrarse cuando el puente se usa en modo detallado.

#### Scenario: Modo detallado
- **WHEN** el puente ejecuta un subcomando en modo detallado
- **THEN** el stderr de Java se reenvía al stderr de Python
