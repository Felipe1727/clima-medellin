# Spec Delta

## Purpose

Estima el PM2.5 a partir de la temperatura, la humedad relativa y el viento con una regresión lineal entrenada sin fuga de información, y la evalúa frente a una línea base con métricas y diagnósticos interpretables.

## ADDED Requirements

### Requirement: Conjunto unido sin nulos
El conjunto de la regresión SHALL contener solo los timestamps UTC que tienen PM2.5 y las tres predictoras no nulas, y SHALL informar del número de filas excluidas.

#### Scenario: Filas incompletas
- **WHEN** de 10 horas, 2 no tienen meteorología y 1 tiene el viento nulo
- **THEN** el conjunto tiene 7 filas y se informan 3 excluidas

### Requirement: Entrenamiento sin fuga de información
El escalador y la regresión SHALL ajustarse solo con las filas del periodo de entrenamiento de la separación temporal; las métricas SHALL calcularse solo con el periodo de prueba, y ninguna fila del hueco de 24 h SHALL usarse.

#### Scenario: Escalador ajustado con el entrenamiento
- **WHEN** se entrena el modelo
- **THEN** las medias aprendidas por el escalador son las medias de las predictoras del entrenamiento

#### Scenario: Separación respetada
- **WHEN** se entrena y evalúa
- **THEN** todas las filas de entrenamiento son anteriores al fin del entrenamiento y todas las de prueba son al menos 24 h posteriores

### Requirement: Línea base y métricas
La línea base SHALL predecir siempre la media del PM2.5 del entrenamiento. Para el modelo y para la línea base SHALL calcularse MAE, RMSE y R² sobre la prueba. El resultado SHALL incluir las fechas exactas de la separación y el número de filas de entrenamiento y de prueba.

#### Scenario: Línea base
- **WHEN** el PM2.5 medio del entrenamiento es 12 µg/m³
- **THEN** la línea base predice 12 µg/m³ en todas las horas de prueba y sus métricas se calculan con esa constante

### Requirement: Coeficientes y diagnósticos
El resultado SHALL incluir el intercepto y los coeficientes estandarizados y en unidades originales, el VIF de cada predictora calculado con el entrenamiento y el estadístico de Durbin-Watson de los residuos de prueba, y SHALL NOT incluir p-valores.

#### Scenario: Coeficientes conocidos
- **WHEN** los datos siguen PM2.5 = 5 + 2·T − 0,1·HR − 3·V con un ruido pequeño
- **THEN** los coeficientes en unidades originales son aproximadamente 2, −0,1 y −3 y el intercepto aproximadamente 5

#### Scenario: Predictoras colineales
- **WHEN** la humedad es casi una función lineal de la temperatura
- **THEN** el VIF de ambas es mayor que 10

### Requirement: Resultados reproducibles
Entrenar y evaluar dos veces con los mismos datos SHALL producir exactamente los mismos coeficientes y métricas.

#### Scenario: Repetición
- **WHEN** se ejecuta dos veces el entrenamiento con el mismo conjunto
- **THEN** los coeficientes y las métricas son idénticos
