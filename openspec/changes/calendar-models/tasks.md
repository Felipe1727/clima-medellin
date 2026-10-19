# Tasks

## 1. Modelos

- [ ] 1.1 Implementar `calendar_features`, `fit_calendar_model(s)` y `CalendarModel` en `clima_medellin/calendar_models.py` con pruebas de medianoche, conversión UTC→local, coeficientes sintéticos recuperados, evaluación independiente de la prueba, determinismo y MAE de temperatura menor que la línea base con las muestras; verificar con `uv run pytest`
- [ ] 1.2 Implementar `parse_moment`, `request_hours` y `predict` con pruebas de solo fecha (24 horas), una hora, rango de 72 horas, límites y formatos inválidos, y tabla con real y diferencia; verificar con `uv run pytest`

## 2. Documentación

- [ ] 2.1 Escribir la sección de modelos de calendario en `docs/regresion.md` (idea, rasgos, receta con coeficientes reales, evaluación con las muestras, límites), D-024 en `docs/decisiones.md`, la Fase 10 en `docs/fases.md` y la sección 10 de `docs/implementacion.md` con fragmentos reales; verificar con `uv run pytest`
- [ ] 2.2 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `calendar-models` como hecho en `openspec/roadmap.md`.
