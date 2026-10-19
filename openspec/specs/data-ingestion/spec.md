# data-ingestion Specification

## Purpose
Descarga las respuestas de Open-Meteo para la ubicación del proyecto y las convierte en tablas horarias validadas, en UTC y en unidades canónicas, listas para entregarse a la capa de persistencia.

## Requirements

### Requirement: Peticiones con los parámetros fijados
El cliente SHALL construir cada petición con el punto `MED-CENTRO` (6.2447, -75.5748), las horas en GMT y el rango de fechas pedido; para ERA5 SHALL usar las variables de temperatura, humedad y viento a 10 m, `models=era5`, `elevation=1495` y `wind_speed_unit=ms`; para CAMS global SHALL usar `pm2_5` y `domains=cams_global`, sin `elevation`.

#### Scenario: Petición de ERA5
- **WHEN** se construye la petición de ERA5 del 2026-03-01 al 2026-03-31
- **THEN** la URL es la de la Historical Weather API e incluye `models=era5`, `elevation=1495`, `wind_speed_unit=ms`, `start_date=2026-03-01` y `end_date=2026-03-31`

#### Scenario: Petición de PM2.5
- **WHEN** se construye la petición de CAMS global
- **THEN** la URL es la de la Air Quality API, incluye `hourly=pm2_5` y `domains=cams_global` y no incluye `elevation`

### Requirement: Reintentos ante fallos transitorios
El cliente SHALL reintentar hasta 3 veces, con una espera que crece en cada intento, cuando la petición agota el tiempo de espera, falla la conexión o la respuesta tiene un estado 5xx. Ante un estado 4xx SHALL fallar sin reintentar. Si se agotan los reintentos SHALL fallar con un error que indique la fuente y el rango.

#### Scenario: Fallo transitorio y éxito
- **WHEN** la API responde 503 dos veces y después 200
- **THEN** el cliente devuelve la respuesta tras 2 reintentos con esperas crecientes

#### Scenario: Reintentos agotados
- **WHEN** la API agota el tiempo de espera en los 4 intentos
- **THEN** el cliente falla con un error que menciona la fuente y el rango

#### Scenario: Error del cliente
- **WHEN** la API responde 400
- **THEN** el cliente falla sin reintentar

### Requirement: Tabla normalizada en UTC con columnas canónicas
La normalización SHALL producir una tabla indexada por timestamps UTC con zona horaria, ordenada y sin timestamps repetidos, con las columnas `temperature_2m_c`, `relative_humidity_2m_pct` y `wind_speed_10m_ms` para ERA5 y `pm25_ug_m3` para CAMS global. Si las unidades de la respuesta no son °C, %, m/s y µg/m³ SHALL fallar.

#### Scenario: Muestra anual de ERA5
- **WHEN** se normaliza `samples/era5_year.json` con fin efectivo a las 00:00 UTC de D−4
- **THEN** la tabla tiene 8 664 filas (8 760 menos las 96 horas no publicadas), índice UTC sin duplicados y las tres columnas canónicas

#### Scenario: Unidad inesperada
- **WHEN** la respuesta declara el viento en km/h
- **THEN** la normalización falla indicando la variable y la unidad

### Requirement: Validación sin inventar valores
Un valor fuera de su rango plausible (temperatura −20..50 °C, humedad 0..100 %, viento 0..75 m/s, PM2.5 0..1000 µg/m³) SHALL convertirse en `null` y contarse por variable; los valores ausentes SHALL conservarse como `null`, nunca como 0.

#### Scenario: Valor imposible
- **WHEN** una copia de la muestra tiene una temperatura de 80 °C
- **THEN** ese valor queda nulo, el resto de la fila se conserva y el informe cuenta 1 valor fuera de rango en la temperatura

#### Scenario: Nulo parcial
- **WHEN** una fila tiene el viento nulo y la temperatura y la humedad presentes
- **THEN** la fila se conserva con el viento nulo

### Requirement: Recortes antes de guardar
La normalización SHALL eliminar los timestamps repetidos dentro de la respuesta (conservando el primero), los timestamps en o después del fin efectivo de la fuente y las filas con todas las variables nulas, y SHALL informar de cuántas filas eliminó por cada motivo.

#### Scenario: Nulos finales de ERA5
- **WHEN** se normaliza `samples/era5_recent_month.json`
- **THEN** no queda ninguna fila en o después de las 00:00 UTC de D−4 y el informe cuenta esas filas

#### Scenario: Fila vacía intermedia
- **WHEN** una fila anterior al fin efectivo tiene todas las variables nulas
- **THEN** se descarta y el informe la cuenta como fila vacía

#### Scenario: Timestamp repetido
- **WHEN** la respuesta contiene dos veces el mismo timestamp
- **THEN** se conserva la primera aparición y el informe cuenta 1 duplicado
