# Design

## Context

`menu.py` imprime texto con `print_fn` y lee con `input_fn`; las tablas son `DataFrame.to_string`. Las decisiones de aspecto y lenguaje están bloqueadas en `openspec/roadmap.md` (segunda exploración).

## Goals / Non-Goals

**Goals:** misma lógica, nueva presentación: `rich`, menú agrupado, paneles «Qué significa», términos traducidos, progreso, salida sin color cuando corresponde.

**Non-Goals:** la pantalla de predicción, la evaluación de los cuatro modelos y la gráfica del efecto de cada hora (`prediction-menu`).

## Decisions

- `ui.py` reúne la presentación: `make_console()` (`Console(highlight=False)`, que respeta `NO_COLOR` y no colorea si la salida no es una terminal), `df_table(frame, title, columns)` (tabla de `rich` desde un DataFrame, números alineados a la derecha), `meaning(text)` (panel «Qué significa»), `ok/warn/error/progress` (prefijos `[OK]`, `[AVISO]`, `[ERROR]`, `[…]` coloreados: el color acompaña siempre a la palabra), `STATE_STYLE` (COMPLETA verde, PARCIAL amarillo, SIN_DATOS rojo) y `TERMS` (traducciones de términos técnicos).
- `Menu(bridge, *, console=None, input_fn=None, ...)`: imprime con `console.print`; si `input_fn` es `None` usa `console.input`. Las pruebas pasan una consola de grabación (`Console(file=StringIO(), width=120, color_system=None)`) y leen el texto exportado.
- Estado de la cabecera en caché: se calcula la primera vez que se muestra el menú y se invalida tras la opción 2, para no lanzar dos JVM cada vez que se muestra el menú. Si el puente falla, el estado es «desconocido».
- Progreso: `rich.progress.Progress` para la descarga (una tarea con tantas unidades como peticiones) y para las gráficas; además se mantiene una línea `[…]` por petición para que el avance quede en el registro.
- La opción 5 conserva su contenido (regresión PM2.5 ← clima) con nombre y términos nuevos; `prediction-menu` añade los modelos de calendario.

## Risks / Trade-offs

- [Tablas anchas en terminales estrechas] → `rich` ajusta las columnas; los títulos de columna son cortos con la traducción en el panel.
- [Las barras de progreso no se ven en la salida grabada] → las líneas `[…]` las sustituyen en las pruebas y en archivos de registro.
