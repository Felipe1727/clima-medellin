# Spec Delta

## ADDED Requirements

### Requirement: Gráfica del efecto de cada hora
El sistema SHALL generar una gráfica de 3 paneles (temperatura, humedad, PM2.5) con el efecto de cada hora local frente a la medianoche según los modelos de calendario, con las unidades en los ejes.

#### Scenario: Efecto de cada hora
- **WHEN** se genera la gráfica con los tres modelos de calendario
- **THEN** tiene 3 paneles de 24 barras cada uno, con título, periodo y atribución

### Requirement: Gráfica de la predicción de un rango
El sistema SHALL generar una gráfica de 3 paneles con la predicción horaria de cada variable, una banda de ± error típico y, cuando existan, los valores reales.

#### Scenario: Rango con valores reales
- **WHEN** se dibuja la predicción de un rango con datos guardados
- **THEN** cada panel tiene la línea de predicción, la banda y la línea de valores reales con leyenda
