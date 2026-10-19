# Spec Delta

## Purpose

Actualiza la base descargando de Open-Meteo solo los intervalos que faltan dentro de la ventana y del fin efectivo de cada fuente, y deja constancia de cada descarga.

## ADDED Requirements

### Requirement: Plan de actualización
El plan SHALL contener, por fuente, las peticiones por rango de fechas que cubren los pasos esperados sin registro, y SHALL estar vacío para una fuente cuyos pasos esperados ya tienen todos registro.

#### Scenario: Segunda actualización inmediata
- **WHEN** se ejecuta una actualización completa y justo después se calcula otro plan
- **THEN** el plan no contiene ninguna petición

#### Scenario: Un día ausente
- **WHEN** a la base le falta un día completo de ERA5 dentro de la ventana
- **THEN** el plan contiene una sola petición de ERA5, de ese día

### Requirement: Ejecución del plan
Cada petición del plan SHALL descargarse, normalizarse, recortarse a [inicio de la ventana, fin efectivo) e importarse como un lote; tras ejecutar el plan SHALL recalcularse la cobertura. Nada en el fin efectivo o después SHALL guardarse.

#### Scenario: Carga inicial
- **WHEN** se actualiza una base vacía con una API que devuelve todas las horas publicadas
- **THEN** las dos fuentes quedan en estado `COMPLETA` y el último timestamp de ERA5 es anterior a las 00:00 UTC de D−4

### Requirement: Intentos vacíos registrados
Si la API no devuelve ningún valor para una petición, SHALL importarse igualmente un lote vacío, de modo que quede un `IngestionBatch` con 0 insertados.

#### Scenario: Intervalo sin datos en la fuente
- **WHEN** la API devuelve solo nulos para una petición
- **THEN** el resultado de esa petición tiene un `batch_id`, 0 recibidos y 0 insertados
