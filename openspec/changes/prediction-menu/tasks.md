# Tasks

## 1. Gráficas y pantallas

- [ ] 1.1 Añadir `plots.hour_effects` y `plots.prediction_chart` con pruebas de paneles, barras, banda, leyenda, título, periodo y atribución; verificar con `uv run pytest`
- [ ] 1.2 Implementar la opción 6 (preguntas, validación, tabla hora a hora con real y diferencia, «valor típico», resumen diario de rangos largos, tabla bajo petición, gráfica, panel «Qué significa»), la opción 5 con los cuatro modelos y la gráfica nueva en la opción 7; verificar con `uv run ruff check .`
- [ ] 1.3 Ampliar `test_menu.py`: día pasado con valores reales, fecha futura, rango de 3 días con resumen y PNG, fecha inválida y límite de 31 días explicados, tabla de cuatro modelos y 14 gráficas; verificar con `uv run pytest`

## 2. Documentación

- [ ] 2.1 Actualizar `docs/cli-y-visualizaciones.md` (opciones 5, 6 y 7, gráficas nuevas), la sección 12 de `docs/implementacion.md` con fragmentos reales, el uso en `README.md` y la Fase 10 completada en `docs/fases.md`; verificar con `uv run pytest`
- [ ] 2.2 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `prediction-menu` como hecho en `openspec/roadmap.md`.
