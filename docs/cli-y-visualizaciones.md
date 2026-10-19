# CLI y visualizaciones

Este documento describe la experiencia del usuario: el menú de la aplicación de terminal, qué hace y qué muestra cada opción, qué gráficas se generan y para qué sirven, y cómo comunica la aplicación su estado y sus errores. Las decisiones que se apoyan en este documento son D-001 y D-023 ([decisiones.md](decisiones.md)). Las ejecuciones de terminal mostradas son **maquetas ficticias**, no salidas reales. El menú está implementado en `python/src/clima_medellin/menu.py` (Fase 9), tal como se describe aquí ([implementacion.md](implementacion.md#9-menú-de-la-cli)).

## Menú principal

Desde la Fase 10 el menú está agrupado por lo que el usuario quiere hacer y usa colores, tablas y explicaciones en lenguaje sencillo (D-025). El estado de la base aparece en la cabecera con una palabra y un color (verde «al día», amarillo «incompleta», rojo «vacía»).

```text
 +----------------------------------------------------------------------------+
 | CLIMA MEDELLÍN · Bases de Datos                                            |
 | Ubicación: Medellín – Centro (MED-CENTRO)                                  |
 | Datos del último año: 2025-10-18 → 2026-10-18 (hora de Medellín)           |
 | Base de datos: al día · las dos fuentes están completas                    |
 +----------------------------------------------------------------------------+
 DATOS
   1  Ver qué datos hay guardados (cobertura)
   2  Descargar los datos que faltan (actualizar)
   3  Consultar registros por fecha
 ANÁLISIS
   4  Resumen estadístico (medias, rangos, franjas)
   5  Evaluar los modelos (qué tan bien predicen)
 PREDICCIONES
   6  Predecir temperatura, humedad o PM2.5 para una fecha u hora
   7  Generar gráficas

   0  Salir

Elige una opción (0-7):
```
*(Aspecto aproximado del menú, sin colores; rich dibuja el recuadro con esquinas redondeadas.)*

## Qué hace cada opción

| # | Opción | Qué hace | Qué muestra en la terminal | Llama a Java |
|---|---|---|---|---|
| 1 | Ver qué datos hay guardados | Calcula la ventana y el fin efectivo de cada fuente, pide a Java lo que existe y calcula métricas y estado ([cobertura-y-franjas.md](cobertura-y-franjas.md#criterio-de-cobertura)) | Una tabla por fuente y variable: horas esperadas, con dato, % de cobertura, hueco más largo y estado (COMPLETA, PARCIAL o SIN_DATOS, con su color y su palabra); además, los intervalos faltantes más grandes | `coverage` |
| 2 | Descargar los datos que faltan | Calcula los faltantes, muestra el plan y pide confirmación. Luego descarga, normaliza, escribe en `staging/` e importa | El plan (tabla), las llamadas estimadas, el progreso por intervalo, el resumen de cada lote (recibidos, insertados, duplicados, rechazados) y la cobertura resultante | `coverage`, `import` |
| 3 | Consultar registros por fecha | Pide la fuente y un rango de fechas locales (con ejemplo); exporta y muestra los registros | Una tabla paginada con la hora local y UTC, los valores (`—` para null) y el lote de origen; al final, el número de registros y de valores nulos | `export` |
| 4 | Resumen estadístico | Exporta la ventana y calcula por variable: datos, sin valor, media, mediana, desviación típica, mínimo, máximo y percentiles; también las medias por franja y los días con dato | Tablas por variable y por franja, con advertencias si la cobertura no es COMPLETA | `export` |
| 5 | Evaluar los modelos | Exporta, une las fuentes, aplica la separación temporal con hueco, entrena y evalúa frente a la línea base ([regresion.md](regresion.md)) | Las fechas de cada conjunto y su tamaño, la tabla «qué tan bien predice» (error típico, R²) del modelo frente a la línea base, los coeficientes con su VIF y el estadístico de Durbin-Watson explicado | `export` |
| 6 | Predecir | Modelos de calendario ([regresion.md](regresion.md#modelos-de-calendario)) | Ver la especificación `prediction-menu` | `export` |
| 7 | Generar gráficas | Pregunta si se muestran en ventana o se guardan como PNG y genera todas las gráficas con una barra de progreso | La ruta de cada PNG | `export`, `coverage` |
| 0 | Salir | Termina la aplicación; no borra nada | Un mensaje de despedida | — |

**Reglas comunes** (implementadas en la Fase 9; con cobertura no COMPLETA, el menú muestra un `[AVISO]` y pregunta `¿Continuar de todos modos? [s/N]`):

- Las opciones 3 a 6 avisan si la cobertura no es COMPLETA, pero no se bloquean: el usuario decide si continuar.
- Con la base vacía, las opciones 3 a 6 sugieren ejecutar primero la opción 2.
- Toda hora mostrada al usuario va en hora local de Medellín, con la UTC al lado cuando sea relevante (opción 3).

## Gráficas

| Gráfica | Pregunta que responde | Datos necesarios |
|---|---|---|
| **Series temporales** (una por variable) | ¿Cómo evolucionaron la temperatura, la humedad, el viento y el PM2.5 durante el año? ¿Hay huecos o saltos raros? | Los registros de la ventana, en hora local; los huecos se dejan como cortes de la línea (sin unir los puntos) |
| **Perfil diurno** | ¿Cuál es el ciclo típico de cada variable a lo largo del día? ¿Coinciden las franjas con los momentos característicos? | La media por hora local (0–23) del **entrenamiento**, con una banda de dispersión y las franjas sombreadas |
| **Comparación por franjas** | ¿Difieren mañana, tarde y noche? | Los valores por franja y día (diagramas de caja), con el número de días válidos |
| **Dispersión de PM2.5 frente a cada predictora** | ¿Hay una relación visible? ¿Es aproximadamente lineal? | Las observaciones unidas (PM2.5 y predictora) del entrenamiento |
| **Matriz de correlación** | ¿Están correlacionadas las predictoras entre sí (multicolinealidad)? | Las 4 variables del entrenamiento |
| **Real frente a predicho** | ¿Cuánto se acerca el modelo? ¿Dónde falla? | Los valores reales y predichos de la prueba: un gráfico de dispersión con la diagonal y y = x, y la serie temporal superpuesta |
| **Residuos** | ¿Hay patrones que el modelo no captura (varianza no constante, autocorrelación)? | Residuos frente a predichos, residuos en el tiempo y un histograma de residuos |
| **Mapa de cobertura** | ¿Dónde están los huecos? | Una matriz de días × horas locales coloreada según el dato (presente, parcial si alguna variable es nula, o ausente), una por fuente |
| **Diagnóstico de empalmes** | ¿Hay saltos artificiales en PM2.5 por el empalme de los pronósticos de CAMS? | El salto absoluto medio de PM2.5 hacia cada hora UTC, con las 00 y 12 UTC destacadas ([fuentes-y-datos.md](fuentes-y-datos.md#empalmes-de-las-ejecuciones-del-pronóstico-00-y-12-utc)) |

Cada gráfica lleva título, ejes con unidades, el periodo y una nota de fuente («Datos: Open-Meteo.com (ERA5, CAMS)»), como exige la atribución ([fuentes-y-datos.md](fuentes-y-datos.md#licencia-y-atribución)). Implementación (Fase 8): `python/src/clima_medellin/plots.py`, explicada en [implementacion.md](implementacion.md#8-gráficas-con-matplotlib). Las gráficas del perfil, la dispersión y la correlación usan solo el entrenamiento; las de real frente a predicho y residuos, solo la prueba.

## Ventana o PNG

| Modo | Cuándo conviene | Consideraciones |
|---|---|---|
| **Ventana interactiva** | Para explorar: hacer zoom en una serie o revisar un hueco | Necesita un entorno gráfico; el programa se detiene hasta cerrar la ventana |
| **PNG** | Para el informe, la presentación o equipos sin pantalla gráfica | Se guarda en `outputs/<gráfica>_<AAAAmmdd-HHMMSS>.png`; si el nombre ya existe se añade `-2`, `-3`…, así nunca se sobrescribe un resultado anterior |

La aplicación pregunta cada vez el modo (DP-10). Si no hay entorno gráfico disponible, guarda el PNG en lugar de fallar y lo avisa con la ruta. Detección (PV-18, resuelto en la Fase 8): no hay ventana si el backend de Matplotlib es de archivo (Agg, pdf, svg…) o si, en Linux, no están definidas ni `DISPLAY` (X11) ni `WAYLAND_DISPLAY` (Wayland).

## Experiencia de usuario en la terminal

Cada pantalla de resultados termina con un panel **«Qué significa»** de dos o tres frases en lenguaje cotidiano (por ejemplo, en la opción 5: «el modelo se equivoca en promedio 5,7 µg/m³; predecir siempre la media se equivoca 6,1: mejora un 6 %»). Los términos técnicos aparecen con su traducción: «error típico (MAE)», «qué tanto explica el modelo (R²)», «redundancia con otras variables (VIF)», «dependencia entre horas seguidas (Durbin-Watson)». Cada pregunta muestra un ejemplo del formato esperado y una respuesta inválida explica qué se esperaba. Con `NO_COLOR` o con la salida redirigida a un archivo, se muestra lo mismo sin colores.

### Mensajes de estado

| Prefijo | Uso | Ejemplo ficticio |
|---|---|---|
| `[OK]` | Operación completada | `[OK] Lote importado: 744 insertados, 24 duplicados omitidos.` |
| `[…]` | Operación en curso | `[…] Descargando ERA5 2026-03-01 → 2026-03-31 (2/5)` |
| `[AVISO]` | No impide continuar, pero hay que saberlo | `[AVISO] Cobertura PARCIAL en PM2.5 (91,2 %). Los resultados pueden estar sesgados.` |
| `[ERROR]` | La operación no se completó | `[ERROR] La base está en uso por otro proceso. Cierra otras ejecuciones e inténtalo de nuevo.` |

### Errores

- **Traducir los errores técnicos.** El código de salida de Java ([arquitectura.md](arquitectura.md#códigos-de-salida)) se convierte en un mensaje comprensible con una sugerencia de acción. Los detalles técnicos (stderr de Java, trazas) se muestran solo en modo detallado o se guardan en un archivo de log.
- **Fallos de red.** Se indica qué intervalo falló, y los intervalos ya importados se conservan. Reintentar la opción 2 solo descarga lo que falta (D-015).
- **Nunca se pierde el estado.** Ningún error deja la base a medias, porque cada import es transaccional (ver [arquitectura.md](arquitectura.md#notas-de-diseño)).

### Confirmaciones

- Antes de descargar: «Se pedirán 5 intervalos (≈ 26 llamadas equivalentes de un máximo de 10 000 diarias). ¿Continuar? [s/N]» *(ficticio)*.
- Antes de un lote de corrección (si se implementa): confirmación explícita, porque modifica registros existentes.
- Las opciones de solo lectura (1, 3, 4, 5 y 6) no piden confirmación.

## Limitaciones y supuestos

- Las maquetas y los mensajes de este documento son ilustrativos; los textos exactos están en `menu.py` y se comprueban en `test_menu.py`.
- La lista de gráficas es definitiva (Fase 8): las 8 previstas más el diagnóstico de empalmes acordado en la exploración. La matriz de correlación se mantiene aunque solapa en parte con el VIF, porque muestra además la relación de cada predictora con PM2.5.
- El comportamiento sin pantalla se prueba con el backend Agg (`test_window_without_display_falls_back_to_png`); la ventana interactiva en el equipo del estudiante depende de que haya un backend gráfico instalado.
- Se supone un único usuario y una sola ejecución a la vez.
