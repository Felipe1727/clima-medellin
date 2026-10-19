# data-coverage Specification

## Purpose
Determina qué datos deberían existir (ventana móvil de un año y fin efectivo de cada fuente) y mide, por variable, cuántos existen, con un estado que indica si bastan para analizar.

## Requirements

### Requirement: Ventana móvil de un año
La ventana SHALL ir desde las 00:00 locales (America/Bogota) del mismo día del año anterior a la fecha D hasta las 00:00 locales de D (exclusivo); si ese día no existe (29 de febrero) SHALL usarse el 28 de febrero del año anterior. Los extremos SHALL expresarse en UTC.

#### Scenario: Días de la ventana
- **WHEN** D es 2026-10-09, 2028-02-29, 2028-03-01 o 2029-03-01
- **THEN** la ventana empieza el 2025-10-09, 2027-02-28, 2027-03-01 o 2028-03-01 y tiene 365, 366, 366 o 365 días respectivamente

#### Scenario: Extremos en UTC
- **WHEN** D es 2026-10-18
- **THEN** la ventana va de 2025-10-18T05:00:00Z a 2026-10-18T05:00:00Z

### Requirement: Fin efectivo por fuente
El fin efectivo de ERA5 SHALL ser el mínimo entre el fin de la ventana y las 00:00 UTC de D−4; el de CAMS global SHALL ser el fin de la ventana.

#### Scenario: Fin efectivo de ERA5
- **WHEN** D es 2026-10-18
- **THEN** el fin efectivo de ERA5 es 2026-10-14T00:00:00Z y el de CAMS global es 2026-10-18T05:00:00Z

### Requirement: Faltantes agrupados en peticiones por fecha
Los pasos esperados SHALL ser todas las horas en punto desde el inicio de la ventana hasta el fin efectivo (exclusivo). Los faltantes (esperados sin registro) SHALL agruparse en intervalos de horas consecutivas, convertirse en rangos de fechas UTC completas y fusionarse cuando se toquen o se solapen.

#### Scenario: Ejemplo de la documentación
- **WHEN** faltan las horas del 3 de marzo de 13:00 a 18:00 UTC y todo el 10 de marzo
- **THEN** se planifican dos peticiones de un día: 3 de marzo y 10 de marzo

#### Scenario: Días contiguos
- **WHEN** faltan las últimas horas del 3 de marzo y las primeras del 4 de marzo
- **THEN** se planifica una sola petición del 3 al 4 de marzo

### Requirement: Métricas y estado de la cobertura
Para cada variable SHALL calcularse dentro de [inicio, fin efectivo): pasos esperados, pasos válidos (con valor no nulo), porcentaje de cobertura, hueco máximo en horas y número de huecos. El estado SHALL ser `SIN_DATOS` si la fuente no tiene ningún registro en la ventana, `COMPLETA` si todas sus variables tienen al menos un 98 % de cobertura y un hueco máximo de 6 h o menos, y `PARCIAL` en cualquier otro caso.

#### Scenario: Cobertura completa con un hueco corto
- **WHEN** a una variable le faltan 6 horas seguidas en una ventana de 8 760 horas y el resto está completo
- **THEN** su cobertura es del 99,93 %, su hueco máximo es 6 h y el estado es `COMPLETA`

#### Scenario: Hueco largo
- **WHEN** a una variable le faltan 7 horas seguidas
- **THEN** el estado es `PARCIAL` aunque la cobertura supere el 98 %

#### Scenario: Porcentaje insuficiente
- **WHEN** una variable tiene un 97 % de cobertura repartida en huecos de 1 hora
- **THEN** el estado es `PARCIAL`

#### Scenario: Sin datos
- **WHEN** la fuente no tiene registros dentro de la ventana
- **THEN** el estado es `SIN_DATOS`
