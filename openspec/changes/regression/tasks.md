# Tasks

## 1. Regresión

- [x] 1.1 Implementar `regression_dataset` en `clima_medellin/regression.py` con la prueba de filas incompletas (10 horas → 7 filas, 3 excluidas); verificar con `uv run pytest`
- [x] 1.2 Implementar `fit_and_evaluate` (Pipeline, línea base, métricas, coeficientes, VIF, Durbin-Watson, predicciones) con pruebas de coeficientes conocidos, escalador ajustado con el entrenamiento, separación con hueco, línea base con la media de entrenamiento, VIF alto con predictoras colineales, reproducibilidad y error con un periodo vacío; verificar con `uv run pytest`

## 2. Documentación

- [x] 2.1 Escribir la sección 7 de `docs/implementacion.md` (unión y nulos, split, Pipeline, métricas, coeficientes en unidades originales, VIF y Durbin-Watson) con fragmentos reales; verificar con `uv run pytest`
- [x] 2.2 Dejar `docs/regresion.md` en su versión final (decisiones, plantilla de interpretación, limitación de los empalmes y resultado con las muestras), marcar la Fase 7 en `docs/fases.md` y actualizar D-017 a D-020 en `docs/decisiones.md`; verificar que no quedan decisiones de la Fase 7 pendientes
- [x] 2.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `regression` como hecho en `openspec/roadmap.md`.
