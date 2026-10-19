# Spec Delta

## Purpose

Divide la ventana de análisis en un periodo de entrenamiento, un hueco de 24 horas y un periodo de prueba, con fechas exactas, para que ninguna decisión derivada de los datos use el periodo de prueba.

## ADDED Requirements

### Requirement: Fechas de la separación temporal
El entrenamiento SHALL ir del inicio de la ventana a las 00:00 locales del mismo día 9 meses naturales después (si ese día no existe, el último día de ese mes); después SHALL descartarse un hueco de 24 horas, y la prueba SHALL ir del final del hueco al fin de la ventana. Todos los extremos SHALL expresarse en UTC y los intervalos SHALL ser semiabiertos.

#### Scenario: Ventana de octubre
- **WHEN** la ventana empieza el 2025-10-18 y termina el 2026-10-18 (hora local)
- **THEN** el entrenamiento va de 2025-10-18T05:00:00Z a 2026-07-18T05:00:00Z, el hueco hasta 2026-07-19T05:00:00Z y la prueba de 2026-07-19T05:00:00Z a 2026-10-18T05:00:00Z

#### Scenario: Día inexistente nueve meses después
- **WHEN** la ventana empieza el 2027-05-31
- **THEN** el entrenamiento termina a las 00:00 locales del 2028-02-29
