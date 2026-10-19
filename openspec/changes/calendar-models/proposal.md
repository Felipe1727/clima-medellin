# Proposal

## Why

El usuario quiere predecir la temperatura, la humedad y el PM2.5 para una hora, un día o un rango de fechas. El modelo existente (PM2.5 a partir del clima) no puede hacerlo: necesita la meteorología de esa hora. La exploración del 2026-10-19 decidió tres **modelos de calendario**, regresiones lineales cuya única entrada es la fecha y hora local, evaluadas honestamente frente a una línea base (ver `openspec/roadmap.md`, decisiones de la segunda exploración).

## What Changes

- Construcción de rasgos de calendario: 23 indicadores de hora del día (00:00 es la referencia) y la onda estacional seno/coseno del día del año.
- Un modelo por variable (temperatura, humedad, PM2.5): ajuste con el entrenamiento, evaluación en la prueba frente a la media de entrenamiento (MAE, RMSE, R²) y reajuste con toda la ventana para predecir; coeficientes en unidades originales (efecto de cada hora y onda estacional).
- Peticiones de predicción en hora local: una hora, un día completo o un rango, con validación de límites (inicio de la ventana … hoy + 365 días, máximo 31 días) y mensajes en español.
- Tabla de predicción con el valor real y la diferencia cuando hay datos guardados.
- Documentación: sección de modelos de calendario en `regresion.md`, D-024, Fase 10 en `fases.md` y sección de `implementacion.md`.

## Capabilities

### New Capabilities
- `calendar-models`: predicción del valor típico de temperatura, humedad y PM2.5 a partir solo de la fecha y hora, con su evaluación.

### Modified Capabilities
<!-- Ninguna: la regresión PM2.5 ← clima no cambia. -->

## Impact

- Código nuevo: `python/src/clima_medellin/calendar_models.py` y sus pruebas.
- Documentación: `docs/regresion.md`, `docs/decisiones.md`, `docs/fases.md`, `docs/implementacion.md`.
