# Tasks

## 1. Separación temporal y tabla de análisis

- [ ] 1.1 Implementar `clima_medellin/split.py` (`add_months`, `temporal_split`, filtros de entrenamiento y prueba) con pruebas de la ventana de octubre y del día inexistente; verificar con `uv run pytest`
- [ ] 1.2 Implementar `clima_medellin/dataset.py` (`combine`, `load_window`) con una prueba de horas de una sola fuente y una prueba con el JAR real que cargue la ventana desde una base temporal; verificar con `uv run pytest`

## 2. Franjas, perfil diurno y estadísticas

- [ ] 2.1 Implementar `clima_medellin/bands.py` (`daily_bands`, `diurnal_profile`) con pruebas sobre un día calculado a mano (ejemplo 17,8 / falta / 19,6 → 18,7, franja NaN con un solo valor, franja de la noche en el día UTC siguiente, PM2.5) y del perfil que excluye la prueba; verificar con `uv run pytest`
- [ ] 2.2 Implementar `clima_medellin/descriptive.py` (`describe_variables`, `describe_bands`) con pruebas de la serie 1–100 con 3 nulos y de los días válidos por franja; verificar con `uv run pytest`

## 3. Documentación

- [ ] 3.1 Escribir la sección 6 de `docs/implementacion.md` (conversión de zona horaria, `groupby` por día local, NaN y mínimo de horas, perfil diurno, percentiles) con fragmentos reales; verificar con `uv run pytest`
- [ ] 3.2 Dejar `docs/cobertura-y-franjas.md` en su versión final (implementación de franjas y perfil), marcar la Fase 6 en `docs/fases.md` y anotar las fechas de la separación en D-018 (`docs/decisiones.md`); verificar que no quedan decisiones de la Fase 6 pendientes
- [ ] 3.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `bands-stats` como hecho en `openspec/roadmap.md`.
