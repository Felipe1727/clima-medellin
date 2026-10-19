# Design

## Context

Las funciones de análisis ya existen: `dataset.load_window` (tabla de las 4 variables), `bands.daily_bands`, `split.temporal_split`, `regression.fit_and_evaluate` (con `predictions` de prueba) y `JavaBridge.coverage` (timestamps con variables no nulas). Las gráficas son PNG estáticos o ventanas de Matplotlib; no hay HTML ni capa de hover.

## Goals / Non-Goals

**Goals:**
- Una función por gráfica que recibe datos ya calculados y devuelve una `Figure` (fácil de probar con Agg).
- Un único punto de salida (`save_or_show`) con la regla de ventana/PNG.

**Non-Goals:**
- Preguntar al usuario el modo de salida (lo hace la CLI, especificación `cli-integration`).
- Modo oscuro o interactividad más allá del zoom de la ventana de Matplotlib.

## Decisions

### Estilo (guía de visualización de datos del proyecto)
- Superficie `#fcfcfb`; tinta principal `#0b0b0b`, secundaria `#52514e`, apagada `#898781`; rejilla en línea continua fina `#e1e0d9`; ejes `#c3c2b7`; sin bordes superior y derecho.
- Una serie por gráfica → color 1 (`#2a78d6`). Dos series (real frente a predicho) → colores 1 y 2 (`#eb6834`), con leyenda. Paleta validada con el script de la guía: todas las comprobaciones pasan (ΔE CVD 24,7, contraste ≥ 3:1).
- Matriz de correlación: divergente azul ↔ rojo (`#2a78d6` ↔ `#e34948`) con punto medio gris `#f0efec`, escala fija −1..1 y el valor en cada celda (es una tabla de 4 × 4).
- Mapa de cobertura: tres clases con leyenda: presente (color 1), parcial (color 2, alguna variable nula) y ausente (gris `#e1e0d9`, que se lee como «nada»).
- Empalmes: barras de color 1 y las de 00 y 12 UTC en color 2 con su valor rotulado; el resto sin números.
- Líneas de 1 px para series horarias densas (8 760 puntos) y de 2 px para perfiles; marcadores pequeños con transparencia en las dispersiones densas.

### Anotación común
- `_finish(fig, title, period)`: título de la figura, texto del periodo debajo y la atribución abajo a la derecha. Los rótulos de los ejes los pone cada gráfica con la unidad entre paréntesis (`UNITS` por columna).

### Huecos
- Las series se reindexan a la rejilla horaria completa del periodo antes de dibujar: las horas sin fila pasan a NaN y Matplotlib corta la línea en los NaN.

### Salida
- `has_display()`: falso si el backend actual no es interactivo (Agg, pdf, svg, ps, cairo, template) o si en Linux no hay `DISPLAY` ni `WAYLAND_DISPLAY`.
- `save_or_show(fig, name, mode, outputs_dir) -> Output(path, notice)`: `mode="png"` guarda; `mode="ventana"` muestra con `plt.show()` si `has_display()`, si no guarda y devuelve el aviso. El nombre lleva la fecha y hora local; si ya existe, se añade `-2`, `-3`…
- Las pruebas usan el backend Agg (`MPLBACKEND=Agg` en `conftest.py`).

## Risks / Trade-offs

- [Mapa de cobertura grande (365 × 24 celdas)] → `imshow` con una matriz numérica; ligero.
- [Paleta divergente no validada por el script categórico] → el script es para paletas categóricas; la divergente usa los polos y el gris documentados en la guía.
