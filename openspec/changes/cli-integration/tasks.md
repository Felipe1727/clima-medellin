# Tasks

## 1. Menú

- [x] 1.1 Implementar `clima_medellin/menu.py` (cabecera, bucle, opciones 1–7, avisos de cobertura, errores sin cerrar) y reescribir `cli.py` (`--version`, `--verbose`, arranque del menú); actualizar `test_cli.py`; verificar con `uv run ruff check .`
- [x] 1.2 Escribir `test_menu.py`: escenario de extremo a extremo (base vacía → cobertura → actualización → consulta → estadísticas → regresión → gráficas PNG → salir) y escenarios cortos (opción inválida, base vacía en la opción 4, actualización cancelada, nada que descargar, aviso de cobertura PARCIAL, error del puente); verificar con `uv run pytest`

## 2. Documentación final

- [x] 2.1 Escribir la sección 9 de `docs/implementacion.md` (menú como capa fina, dependencias inyectables, prueba de extremo a extremo) con fragmentos reales y hacer la revisión final del documento (índice completo, todos los fragmentos verificados); verificar con `uv run pytest`
- [x] 2.2 Actualizar `README.md` (estado, instalación y ejecución, requisitos, atribución, limitaciones), `docs/cli-y-visualizaciones.md` (menú implementado), `docs/arquitectura.md` (referencias obsoletas) y `docs/fases.md` (Fase 9 y estado final de todas las fases); verificar que no queda ningún `[Por verificar]` sin resolver o justificar
- [ ] 2.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `cli-integration` como hecho en `openspec/roadmap.md`.
