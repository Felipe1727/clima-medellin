# interactive-menu Specification

## Purpose
Ofrece al usuario, en un menú de terminal en español, todas las operaciones de la aplicación: cobertura, actualización incremental, consulta de registros, estadísticas, regresión y gráficas.

## Requirements

### Requirement: Menú principal
El menú SHALL mostrar una cabecera con la ubicación, la ventana actual en hora de Medellín y el estado de la base, y las opciones agrupadas DATOS (1 Ver qué datos hay guardados, 2 Descargar los datos que faltan, 3 Consultar registros por fecha), ANÁLISIS (4 Resumen estadístico, 5 Evaluar los modelos), PREDICCIONES (6 Predecir temperatura, humedad o PM2.5 para una fecha u hora, 7 Generar gráficas) y 0 Salir. Una opción inválida SHALL mostrar un error y volver a pedir la opción.

#### Scenario: Opción inválida
- **WHEN** el usuario escribe `9`
- **THEN** se muestra un mensaje `[ERROR]` y el menú vuelve a pedir una opción

#### Scenario: Salir
- **WHEN** el usuario escribe `0`
- **THEN** se muestra un mensaje de despedida y la aplicación termina

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
La opción 4 SHALL mostrar las estadísticas por variable y por franja; la opción 5 SHALL mostrar una tabla con los tres modelos de calendario y la regresión PM2.5 ← clima, cada uno frente a su línea base (error típico de ambos, mejora y R²), seguida de las fechas de la separación, el número de filas, las métricas, los coeficientes, el VIF y el estadístico de Durbin-Watson de la regresión con el clima; la opción 7 SHALL preguntar si mostrar en ventana o guardar como PNG y generar todas las gráficas, incluida la del efecto de cada hora, informando de cada PNG guardado y de cualquier aviso.

#### Scenario: Gráficas en PNG
- **WHEN** se elige la opción 7 y el modo PNG con datos cargados
- **THEN** se guardan 14 PNG en la carpeta de salidas y se muestra la ruta de cada uno

#### Scenario: Evaluación de los cuatro modelos
- **WHEN** se elige la opción 5 con datos cargados
- **THEN** la primera tabla tiene una fila por modelo (temperatura, humedad y PM2.5 de calendario, y PM2.5 a partir del clima) con su error típico y el de su línea base

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

### Requirement: Estado de la base en la cabecera
La cabecera SHALL indicar el estado de la base con una palabra y un color: «al día» (verde) si las dos fuentes están `COMPLETA`, «incompleta» (amarillo) si alguna no lo está, «vacía» (rojo) si las dos están `SIN_DATOS`, junto con lo que conviene hacer.

#### Scenario: Base vacía
- **WHEN** se abre el menú con la base vacía
- **THEN** la cabecera dice «vacía» y sugiere la opción 2

### Requirement: Explicaciones en lenguaje sencillo
Cada pantalla de resultados (opciones 1 a 5 y 7) SHALL terminar con un panel «Qué significa» de dos o tres frases en lenguaje cotidiano, y los términos técnicos SHALL mostrarse con su traducción («error típico (MAE)», «qué tanto explica el modelo (R²)», «redundancia con otras variables (VIF)»).

#### Scenario: Evaluación del modelo
- **WHEN** se elige la opción 5
- **THEN** la tabla de métricas usa «error típico (MAE)» y la pantalla termina con un panel «Qué significa» que compara el modelo con la línea base en palabras

### Requirement: Entradas con ejemplo
Cada pregunta que espera un dato SHALL mostrar un ejemplo del formato, y una respuesta inválida SHALL explicar qué se esperaba.

#### Scenario: Fecha inválida
- **WHEN** en la consulta de registros se escribe `03/01/2026`
- **THEN** se muestra un error que indica el formato `AAAA-MM-DD` con un ejemplo

### Requirement: Progreso de operaciones largas
La descarga de datos y la generación de gráficas SHALL mostrar el progreso.

#### Scenario: Descarga
- **WHEN** se ejecuta una actualización con dos peticiones
- **THEN** se muestra el avance de cada petición (1/2, 2/2)

### Requirement: Salida sin colores
Con la variable de entorno `NO_COLOR` o cuando la salida no es una terminal, la interfaz SHALL mostrar el mismo contenido sin códigos de color.

#### Scenario: Salida redirigida
- **WHEN** la salida del menú se escribe en un archivo
- **THEN** el archivo no contiene secuencias de escape de color

### Requirement: Predicción con los modelos de calendario
La opción 6 SHALL pedir «Desde» y «Hasta» (con ejemplo; Enter = solo esa fecha u hora), validar la petición con los límites de los modelos de calendario y mostrar, por hora local, la temperatura, la humedad y el PM2.5 predichos con su error típico. En las horas con datos guardados SHALL mostrar además el valor real y la diferencia; en las demás, la predicción se presenta como «valor típico». La pantalla SHALL terminar con un panel «Qué significa».

#### Scenario: Día pasado
- **WHEN** se pide un día de la ventana con datos guardados
- **THEN** se muestran sus 24 horas con predicción, valor real y diferencia

#### Scenario: Fecha futura
- **WHEN** se pide una fecha posterior a hoy
- **THEN** se muestran las predicciones como «valor típico», sin valores reales

#### Scenario: Petición inválida
- **WHEN** se escribe una fecha con formato inválido o un rango de más de 31 días
- **THEN** se muestra un `[ERROR]` que explica el formato o el límite y se vuelve al menú

### Requirement: Rangos largos
Para peticiones de más de 2 días, la opción 6 SHALL mostrar un resumen diario (media, mínimo y máximo de cada variable), ofrecer la tabla hora a hora (`[s/N]`) y generar una gráfica de la predicción en ventana o PNG según la elección del usuario.

#### Scenario: Rango de 3 días
- **WHEN** se pide del 2026-11-03 al 2026-11-05 y se elige PNG
- **THEN** se muestra un resumen de 3 días y se guarda la gráfica de la predicción
