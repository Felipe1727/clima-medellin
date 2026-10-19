# Proposal

## Why

La CLI funciona, pero es texto plano y usa términos técnicos (MAE, R², VIF, cobertura) sin explicarlos. La segunda exploración (2026-10-19) pidió una interfaz atractiva y comprensible para personas sin formación técnica: colores, tablas formateadas, un menú agrupado por lo que el usuario quiere hacer y explicaciones en lenguaje sencillo (ver `openspec/roadmap.md`).

## What Changes

- Dependencia `rich` para la interfaz de terminal.
- Menú agrupado (DATOS / ANÁLISIS / PREDICCIONES) con 0 = Salir; las gráficas pasan de la opción 6 a la 7 y la opción 6 (predicciones) muestra «próximamente» hasta `prediction-menu`.
- Cabecera con la ubicación, la ventana y el estado de la base en color y con palabra (al día / incompleta / vacía).
- Tablas de `rich` en todas las pantallas; barras de progreso en la descarga y en la generación de gráficas.
- Panel «Qué significa» al final de cada pantalla de resultados; términos técnicos traducidos la primera vez («error típico (MAE)», «qué tanto explica el modelo (R²)»…); entradas con ejemplo y errores de formato explicados.
- Sin colores con `NO_COLOR` ni cuando la salida no es una terminal.
- Documentación: D-025, `cli-y-visualizaciones.md` (menú y pantallas), sección 11 de `implementacion.md`.

## Capabilities

### New Capabilities
<!-- Ninguna. -->

### Modified Capabilities
- `interactive-menu`: menú reagrupado con 0 = Salir, gráficas en la opción 7, cabecera con estado, paneles «Qué significa», lenguaje sencillo, progreso y salida sin colores cuando corresponde.
- `app-cli`: la salida del menú es la opción 0.

## Impact

- Código: `python/src/clima_medellin/ui.py` (nuevo), `menu.py` y `cli.py`; pruebas del menú adaptadas a una consola de grabación.
- Dependencias: `rich`.
- Documentación: `docs/decisiones.md`, `docs/cli-y-visualizaciones.md`, `docs/implementacion.md`, `docs/fases.md`, `README.md`.
