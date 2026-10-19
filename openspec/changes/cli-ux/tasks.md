# Tasks

## 1. Interfaz

- [x] 1.1 Añadir `rich` y crear `clima_medellin/ui.py` (consola, tablas desde DataFrame, panel «Qué significa», prefijos con color y palabra, estilos de estado, traducciones de términos) con pruebas de salida sin color (`NO_COLOR` y archivo); verificar con `uv run pytest`
- [x] 1.2 Rehacer `menu.py` con `rich`: menú agrupado con 0 = Salir, cabecera con estado en caché, tablas, paneles «Qué significa» en las opciones 1–5 y 7, entradas con ejemplo y errores explicados, progreso en descarga y gráficas, opción 6 «próximamente»; actualizar `cli.py`; verificar con `uv run ruff check .`
- [x] 1.3 Adaptar `test_menu.py` y `test_cli.py` a la consola de grabación (extremo a extremo, opción inválida, salida con 0, cabecera vacía, opción 6, fecha inválida explicada, paneles «Qué significa»); verificar con `uv run pytest`

## 2. Documentación

- [x] 2.1 Escribir D-025, actualizar `docs/cli-y-visualizaciones.md` (menú y pantallas nuevas), la sección 11 de `docs/implementacion.md` con fragmentos reales, `docs/fases.md` (Fase 10) y el menú del `README.md`; verificar con `uv run pytest`
- [x] 2.2 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `cli-ux` como hecho en `openspec/roadmap.md`.
