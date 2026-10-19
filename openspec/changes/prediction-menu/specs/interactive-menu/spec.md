# Spec Delta

## MODIFIED Requirements

### Requirement: Estadísticas, regresión y gráficas
La opción 4 SHALL mostrar las estadísticas por variable y por franja; la opción 5 SHALL mostrar una tabla con los tres modelos de calendario y la regresión PM2.5 ← clima, cada uno frente a su línea base (error típico de ambos, mejora y R²), seguida de las fechas de la separación, el número de filas, las métricas, los coeficientes, el VIF y el estadístico de Durbin-Watson de la regresión con el clima; la opción 7 SHALL preguntar si mostrar en ventana o guardar como PNG y generar todas las gráficas, incluida la del efecto de cada hora, informando de cada PNG guardado y de cualquier aviso.

#### Scenario: Gráficas en PNG
- **WHEN** se elige la opción 7 y el modo PNG con datos cargados
- **THEN** se guardan 14 PNG en la carpeta de salidas y se muestra la ruta de cada uno

#### Scenario: Evaluación de los cuatro modelos
- **WHEN** se elige la opción 5 con datos cargados
- **THEN** la primera tabla tiene una fila por modelo (temperatura, humedad y PM2.5 de calendario, y PM2.5 a partir del clima) con su error típico y el de su línea base

## REMOVED Requirements

### Requirement: Opción de predicción pendiente
**Reason**: la predicción ya está disponible.
**Migration**: sustituida por el requisito «Predicción con los modelos de calendario».

## ADDED Requirements

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
