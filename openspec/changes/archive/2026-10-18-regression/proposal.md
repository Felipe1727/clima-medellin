# Proposal

## Why

La pregunta central del proyecto es en qué medida la temperatura, la humedad y el viento permiten estimar el PM2.5 en los modelos ERA5 y CAMS. La Fase 7 implementa la regresión lineal descrita en [regresion.md](../../../docs/regresion.md): conjunto unido, separación temporal sin fuga, Pipeline, línea base, métricas y diagnósticos, para que la opción 5 del menú y las gráficas de resultados tengan qué mostrar.

## What Changes

- Conjunto de la regresión: unión interna de PM2.5 y meteorología por timestamp UTC, sin filas con algún nulo, informando cuántas filas se excluyen y por qué.
- Entrenamiento y evaluación: separación temporal de D-018 (`split.py`), `Pipeline(StandardScaler, LinearRegression)` ajustado solo con el entrenamiento, línea base = media del PM2.5 de entrenamiento, MAE, RMSE y R² del modelo y de la línea base sobre la prueba.
- Coeficientes estandarizados y en unidades originales, VIF de las predictoras (entrenamiento) y Durbin-Watson de los residuos de prueba; sin p-valores.
- Resultado con las fechas exactas de la separación, los tamaños de cada conjunto y las predicciones y residuos de prueba (para las gráficas).
- Documentación: sección 7 de `docs/implementacion.md`, `docs/regresion.md` final (decisiones, plantilla de interpretación, limitación de los empalmes y resultado con las muestras), Fase 7 en `docs/fases.md`.

## Capabilities

### New Capabilities
- `pm25-regression`: entrenamiento y evaluación de la regresión lineal de PM2.5 frente a la meteorología, con línea base, métricas y diagnósticos.

### Modified Capabilities
<!-- Ninguna: se reutiliza temporal-split sin cambiar sus requisitos. -->

## Impact

- Código nuevo: `python/src/clima_medellin/regression.py` y sus pruebas.
- Documentación: `docs/implementacion.md`, `docs/regresion.md`, `docs/fases.md`, `docs/decisiones.md`.
