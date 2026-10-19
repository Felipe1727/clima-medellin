# api-samples Specification

## Purpose
Proporciona respuestas reales de Open-Meteo, descargadas de forma reproducible y versionadas en `samples/`, que documentan el formato de las APIs y sirven de datos de prueba sin red.

## Requirements

### Requirement: Descarga reproducible de muestras
El script de muestras SHALL descargar cuatro respuestas con los parámetros fijados del proyecto (punto `MED-CENTRO` 6.2447, -75.5748; ERA5 con `models=era5`, `elevation=1495` y `wind_speed_unit=ms`; PM2.5 con `domains=cams_global`; horas en GMT) y SHALL guardarlas en `samples/` junto con un `samples/README.md` que indique para cada archivo la URL, los parámetros y la fecha de descarga.

#### Scenario: Ejecución del script
- **WHEN** se ejecuta `uv run python scripts/fetch_samples.py` con conexión a internet
- **THEN** se escriben `era5_year.json`, `era5_recent_month.json`, `cams_pm25_year.json`, `cams_pm25_last_week.json` y `README.md` en `samples/`

#### Scenario: Rangos relativos a la fecha local
- **WHEN** el script se ejecuta en la fecha D de America/Bogota
- **THEN** las muestras anuales cubren de D−1 año a D−1 día, la mensual de ERA5 cubre los 30 días anteriores a D y la semanal de PM2.5 los 7 días anteriores a D

### Requirement: Propiedades verificadas de las muestras
La batería de pruebas SHALL verificar, sin acceder a la red, que las muestras versionadas tienen timestamps horarios consecutivos en GMT, las unidades esperadas (°C, %, m/s, µg/m³), 8 760 u 8 784 pasos en las muestras anuales, 24 valores por día y ningún nulo en la muestra anual de PM2.5, y nulos finales en la muestra mensual de ERA5 a partir del día D−4.

#### Scenario: Muestra anual de ERA5
- **WHEN** se carga `samples/era5_year.json`
- **THEN** tiene 8 760 u 8 784 timestamps horarios consecutivos y las unidades °C, % y m/s

#### Scenario: Muestra anual de PM2.5
- **WHEN** se carga `samples/cams_pm25_year.json`
- **THEN** tiene 24 valores por día, ninguno nulo, en µg/m³

#### Scenario: Nulos finales de ERA5
- **WHEN** se carga `samples/era5_recent_month.json`
- **THEN** todos los valores desde las 00:00 UTC del día D−4 son nulos y los anteriores no lo son
