# descriptive-analysis Specification

## Purpose
Describe las cuatro variables de la ventana: franjas de mañana, tarde y noche por día civil de Medellín, perfil diurno por hora local y estadísticas descriptivas, sin interpolar ni ocultar la falta de datos.

## Requirements

### Requirement: Tabla de análisis de la ventana
La tabla de análisis SHALL unir por timestamp UTC los registros exportados de ERA5 y de CAMS global dentro de la ventana, con las columnas `temperature_2m_c`, `relative_humidity_2m_pct`, `wind_speed_10m_ms` y `pm25_ug_m3`, conservando las horas que solo tienen una de las dos fuentes.

#### Scenario: Horas de una sola fuente
- **WHEN** una hora tiene PM2.5 pero no meteorología
- **THEN** aparece en la tabla con las tres variables meteorológicas nulas

### Requirement: Franjas por día civil local
Para cada día civil de America/Bogota y cada variable, las franjas mañana (07–09 h), tarde (13–15 h) y noche (19–21 h) SHALL valer el promedio de los valores no nulos de sus tres horas locales, o NaN si hay menos de 2 valores válidos; no SHALL interpolarse.

#### Scenario: Ejemplo de la documentación
- **WHEN** el 12 de abril la temperatura es 17,8 °C a las 07:00, falta a las 08:00 y es 19,6 °C a las 09:00 (hora local)
- **THEN** la franja de la mañana de ese día vale 18,7 °C

#### Scenario: Franja con un solo valor
- **WHEN** solo una de las tres horas de una franja tiene valor
- **THEN** la franja vale NaN

#### Scenario: Franja de la noche
- **WHEN** hay valores a las 00:00, 01:00 y 02:00 UTC del 13 de abril
- **THEN** forman la franja de la noche del 12 de abril (19–21 h locales)

### Requirement: Perfil diurno con el entrenamiento
El perfil diurno SHALL dar, para cada hora local de 0 a 23 y cada variable, la media de los valores no nulos del periodo de entrenamiento y el número de valores válidos usados.

#### Scenario: Datos de prueba excluidos
- **WHEN** las horas del periodo de prueba tienen valores distintos de las del entrenamiento
- **THEN** el perfil diurno solo refleja los valores del entrenamiento

### Requirement: Estadísticas descriptivas
Para cada variable SHALL calcularse el número de valores válidos, el número de nulos, la media, la mediana, la desviación estándar, el mínimo, el máximo y los percentiles 5, 25, 75 y 95; y para cada variable y franja, la media de las franjas válidas y el número de días válidos.

#### Scenario: Serie conocida
- **WHEN** una variable toma los valores 1 a 100 y además tiene 3 nulos
- **THEN** n es 100, nulos es 3, la media es 50,5, la mediana 50,5, el mínimo 1, el máximo 100 y el percentil 25 es 25,75

#### Scenario: Días válidos por franja
- **WHEN** la franja de la mañana es válida en 2 de 3 días
- **THEN** la estadística de esa franja indica 2 días válidos
