# Spec Delta

## Purpose

Ofrece al usuario, en un menú de terminal en español, todas las operaciones de la aplicación: cobertura, actualización incremental, consulta de registros, estadísticas, regresión y gráficas.

## ADDED Requirements

### Requirement: Menú principal
El menú SHALL mostrar una cabecera con la ubicación y la ventana actual en hora de Medellín, y las opciones 1 Verificar cobertura, 2 Actualizar datos, 3 Consultar registros, 4 Estadísticas descriptivas, 5 Entrenar y evaluar la regresión, 6 Generar visualizaciones y 7 Salir. Una opción inválida SHALL mostrar un error y volver a pedir la opción.

#### Scenario: Opción inválida
- **WHEN** el usuario escribe `9`
- **THEN** se muestra un mensaje `[ERROR]` y el menú vuelve a pedir una opción

### Requirement: Verificar cobertura
La opción 1 SHALL mostrar, por fuente y variable, los pasos esperados, válidos, el porcentaje de cobertura, el hueco máximo y el estado, y los intervalos faltantes más grandes.

#### Scenario: Base vacía
- **WHEN** se elige la opción 1 con la base vacía
- **THEN** las dos fuentes aparecen con estado `SIN_DATOS`

### Requirement: Actualizar datos
La opción 2 SHALL mostrar el plan (peticiones por fuente y rango, y llamadas equivalentes estimadas), pedir confirmación `[s/N]` y, si se confirma, descargar e importar cada petición mostrando su progreso y el resumen del lote (recibidos, insertados, duplicados, rechazados), y al final la cobertura resultante. Si una petición falla SHALL mostrarse qué intervalo falló y continuar con las demás; si el plan está vacío SHALL indicarse que no hay nada que descargar.

#### Scenario: Actualización confirmada
- **WHEN** se elige la opción 2 con la base vacía y se responde `s`
- **THEN** se importa un lote por fuente y la cobertura resultante se muestra

#### Scenario: Actualización cancelada
- **WHEN** se elige la opción 2 y se responde `N` o se pulsa Enter
- **THEN** no se descarga nada

#### Scenario: Nada que descargar
- **WHEN** se elige la opción 2 con la base al día
- **THEN** se indica que no hay nada que descargar y no se pide confirmación

### Requirement: Consultar registros
La opción 3 SHALL pedir una fuente y un rango de fechas locales (inclusive) y mostrar una tabla paginada con la hora local, la hora UTC, los valores (`—` para nulo) y el lote de origen, y al final el número de registros y de valores nulos.

#### Scenario: Consulta de un día
- **WHEN** se consulta un día completo de ERA5 guardado
- **THEN** se muestran sus 24 registros en páginas y el total de registros

### Requirement: Estadísticas, regresión y gráficas
La opción 4 SHALL mostrar las estadísticas por variable y por franja; la opción 5 SHALL mostrar las fechas de la separación, el número de filas, las métricas del modelo y de la línea base, los coeficientes, el VIF y el estadístico de Durbin-Watson; la opción 6 SHALL preguntar si mostrar en ventana o guardar como PNG y generar todas las gráficas, informando de cada PNG guardado y de cualquier aviso.

#### Scenario: Gráficas en PNG
- **WHEN** se elige la opción 6 y el modo PNG con datos cargados
- **THEN** se guardan los PNG en la carpeta de salidas y se muestra la ruta de cada uno

### Requirement: Avisos de cobertura y base vacía
Antes de las opciones 3 a 6, si alguna fuente no tiene cobertura `COMPLETA` SHALL mostrarse un `[AVISO]` y preguntarse si continuar; si las dos fuentes están en `SIN_DATOS` SHALL sugerirse la opción 2 y volver al menú.

#### Scenario: Base vacía en la opción 4
- **WHEN** se elige la opción 4 con la base vacía
- **THEN** se sugiere ejecutar primero la opción 2 y se vuelve al menú

### Requirement: Errores sin cerrar la aplicación
Un error del puente con Java, de la API o del análisis SHALL mostrarse como `[ERROR]` con su mensaje en español y SHALL devolver al menú.

#### Scenario: Base en uso
- **WHEN** el JAR responde que la base está en uso
- **THEN** se muestra `[ERROR]` con el mensaje traducido y el menú sigue disponible
