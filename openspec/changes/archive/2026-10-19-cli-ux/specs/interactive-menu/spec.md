# Spec Delta

## MODIFIED Requirements

### Requirement: Menú principal
El menú SHALL mostrar una cabecera con la ubicación, la ventana actual en hora de Medellín y el estado de la base, y las opciones agrupadas DATOS (1 Ver qué datos hay guardados, 2 Descargar los datos que faltan, 3 Consultar registros por fecha), ANÁLISIS (4 Resumen estadístico, 5 Evaluar los modelos), PREDICCIONES (6 Predecir temperatura, humedad o PM2.5 para una fecha u hora, 7 Generar gráficas) y 0 Salir. Una opción inválida SHALL mostrar un error y volver a pedir la opción.

#### Scenario: Opción inválida
- **WHEN** el usuario escribe `9`
- **THEN** se muestra un mensaje `[ERROR]` y el menú vuelve a pedir una opción

#### Scenario: Salir
- **WHEN** el usuario escribe `0`
- **THEN** se muestra un mensaje de despedida y la aplicación termina

### Requirement: Estadísticas, regresión y gráficas
La opción 4 SHALL mostrar las estadísticas por variable y por franja; la opción 5 SHALL mostrar las fechas de la separación, el número de filas, las métricas del modelo y de la línea base, los coeficientes, el VIF y el estadístico de Durbin-Watson; la opción 7 SHALL preguntar si mostrar en ventana o guardar como PNG y generar todas las gráficas, informando de cada PNG guardado y de cualquier aviso.

#### Scenario: Gráficas en PNG
- **WHEN** se elige la opción 7 y el modo PNG con datos cargados
- **THEN** se guardan los PNG en la carpeta de salidas y se muestra la ruta de cada uno

## ADDED Requirements

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

### Requirement: Opción de predicción pendiente
Mientras la predicción no esté disponible, la opción 6 SHALL indicar que estará disponible próximamente y volver al menú.

#### Scenario: Opción 6
- **WHEN** se elige la opción 6
- **THEN** se indica que la función estará disponible próximamente

### Requirement: Salida sin colores
Con la variable de entorno `NO_COLOR` o cuando la salida no es una terminal, la interfaz SHALL mostrar el mismo contenido sin códigos de color.

#### Scenario: Salida redirigida
- **WHEN** la salida del menú se escribe en un archivo
- **THEN** el archivo no contiene secuencias de escape de color
