# calendar-models Specification

## Purpose
Predice el valor típico de temperatura, humedad relativa y PM2.5 para cualquier hora, día o rango de hasta 31 días usando solo la fecha y la hora local, e informa de su error típico frente a una línea base.

## Requirements

### Requirement: Rasgos de calendario
Para cada instante SHALL calcularse, en hora de Medellín, 23 indicadores de hora (`h01`…`h23`, todos a 0 a las 00:00) y la onda estacional `sin` y `cos` de 2π·día_del_año/365,25.

#### Scenario: Medianoche
- **WHEN** se calculan los rasgos de las 00:00 locales
- **THEN** los 23 indicadores valen 0

#### Scenario: Hora UTC convertida
- **WHEN** se calculan los rasgos de 2026-03-15T20:00:00Z
- **THEN** solo el indicador `h15` vale 1 (15:00 en Medellín)

### Requirement: Ajuste, evaluación y reajuste
Para temperatura, humedad y PM2.5 SHALL ajustarse una regresión lineal sin escalador con las filas no nulas del entrenamiento, evaluarse en la prueba (MAE, RMSE, R²) frente a la línea base (media del entrenamiento) y reajustarse con todas las filas de la ventana para predecir. El error típico de cada modelo SHALL ser su MAE de prueba.

#### Scenario: Evaluación sin la prueba
- **WHEN** se cambian los valores del periodo de prueba
- **THEN** los coeficientes del modelo de evaluación no cambian

#### Scenario: Coeficientes conocidos
- **WHEN** los datos siguen valor = 20 + efecto_por_hora + 1·sin(estación) − 2·cos(estación) sin ruido
- **THEN** los efectos por hora y los coeficientes estacionales recuperados coinciden con los usados

#### Scenario: Muestras reales
- **WHEN** se evalúa el modelo de temperatura con las muestras y la ventana de D = 2026-10-18
- **THEN** su MAE de prueba es menor que el de su línea base

### Requirement: Peticiones de predicción
Una petición SHALL tener «desde» y opcionalmente «hasta», en hora local, con los formatos `AAAA-MM-DD`, `AAAA-MM-DD HH` o `AAAA-MM-DD HH:MM`. Una fecha sin hora SHALL significar el día completo (desde las 00:00; hasta las 23:00). Sin «hasta», SHALL predecirse solo esa hora o ese día. Las horas SHALL ir del inicio de la ventana a hoy + 365 días y abarcar como máximo 31 días; si no, SHALL fallar con un mensaje en español que explique el límite.

#### Scenario: Solo una fecha
- **WHEN** se pide `2026-11-03` sin «hasta»
- **THEN** se predicen las 24 horas de ese día, de 00:00 a 23:00 locales

#### Scenario: Una hora
- **WHEN** se pide `2026-11-03 15:00` sin «hasta»
- **THEN** se predice una sola hora

#### Scenario: Rango de fechas
- **WHEN** se pide de `2026-11-03` a `2026-11-05`
- **THEN** se predicen 72 horas, con los dos extremos incluidos

#### Scenario: Límites
- **WHEN** se pide un rango de más de 31 días, una fecha anterior a la ventana, una posterior a hoy + 365 días, un «hasta» anterior al «desde» o un formato inválido
- **THEN** la petición falla con un mensaje en español que indica el problema

### Requirement: Tabla de predicción
La predicción SHALL devolver, por hora local, la predicción de cada variable y, cuando hay un valor guardado para esa hora, el valor real y la diferencia (real − predicción).

#### Scenario: Hora con dato guardado
- **WHEN** se predice una hora de la ventana con datos guardados
- **THEN** la fila incluye la predicción, el valor real y la diferencia de cada variable

#### Scenario: Hora futura
- **WHEN** se predice una hora futura
- **THEN** la fila solo tiene predicciones y el valor real queda nulo
