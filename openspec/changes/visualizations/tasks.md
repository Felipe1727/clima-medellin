# Tasks

## 1. Gráficas

- [x] 1.1 Implementar en `clima_medellin/plots.py` el estilo común, la anotación (`_finish`), la salida (`has_display`, `save_or_show`) y `conftest.py` con el backend Agg, con pruebas de PNG con el patrón de nombre, nombre no sobrescrito y aviso sin pantalla; verificar con `uv run pytest`
- [x] 1.2 Implementar las gráficas de datos (series temporales con huecos, perfil diurno con banda y franjas, cajas por franja, dispersión, correlación, mapa de cobertura, empalmes) con pruebas de anotación, hueco no unido y 24 barras con 00 y 12 destacadas; verificar con `uv run pytest`
- [x] 1.3 Implementar las gráficas de la regresión (real frente a predicho, residuos) con pruebas de anotación y de datos solo de prueba; generar todas las gráficas con las muestras y revisarlas visualmente; verificar con `uv run pytest`

## 2. Documentación

- [ ] 2.1 Escribir la sección 8 de `docs/implementacion.md` (anatomía de una figura, huecos, backends, PNG) con fragmentos reales; verificar con `uv run pytest`
- [ ] 2.2 Actualizar `docs/cli-y-visualizaciones.md` (lista definitiva con la gráfica de empalmes, salida, PV-18), `docs/fases.md` (Fase 8) y `docs/decisiones.md` (D-023); verificar que no quedan `[Por verificar, Fase 8]`
- [ ] 2.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `visualizations` como hecho en `openspec/roadmap.md`.
