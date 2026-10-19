# CLI y visualizaciones

Este documento describe la experiencia del usuario: el menú de la aplicación de terminal, qué hace y qué muestra cada opción, qué gráficas se generan y para qué sirven, y cómo comunica la aplicación su estado y sus errores. Las decisiones que se apoyan en este documento son D-001 y D-023 ([decisiones.md](decisiones.md)). Las ejecuciones de terminal mostradas son **maquetas ficticias**, no salidas reales.

## Menú principal

```text
  CLIMA MEDELLÍN · Bases de Datos
  Ubicación: MED-CENTRO · Ventana: 2025-10-09 → 2026-10-09 (America/Bogota)

  1) Verificar cobertura
  2) Actualizar datos
  3) Consultar registros
  4) Estadísticas descriptivas
  5) Entrenar y evaluar la regresión
  6) Generar visualizaciones
  7) Salir

  Opción: _
```
*(Maqueta ficticia.)*

## Qué hace cada opción

| # | Opción | Qué hace | Qué muestra en la terminal | Llama a Java |
|---|---|---|---|---|
| 1 | Verificar cobertura | Calcula la ventana y el fin efectivo de cada fuente, pide a Java lo que existe y calcula métricas y estado ([cobertura-y-franjas.md](cobertura-y-franjas.md#criterio-de-cobertura)) | Una tabla por fuente y variable: esperados, válidos, % de cobertura, hueco máximo y estado (COMPLETA, PARCIAL o SIN_DATOS); además, los intervalos faltantes más grandes | `coverage` |
| 2 | Actualizar datos | Calcula los faltantes, muestra un resumen de lo que va a descargar y pide confirmación. Luego descarga, normaliza, escribe en `staging/` e importa | El plan de descarga (intervalos y llamadas estimadas), el progreso por intervalo, el resumen del lote (recibidos, insertados, duplicados, rechazados) y la cobertura resultante | `coverage`, `import` |
| 3 | Consultar registros | Pide un rango de fechas locales y una fuente; exporta y muestra los registros | Una tabla paginada con la hora local y UTC, los valores (`—` para null) y el lote de origen; al final, el número de registros y de valores nulos | `export` |
| 4 | Estadísticas descriptivas | Exporta la ventana y calcula por variable: n, nulos, media, mediana, desviación, mínimo, máximo y percentiles; también las medias por franja y el número de días válidos | Tablas por variable y por franja, con advertencias si la cobertura no es COMPLETA | `export` |
| 5 | Entrenar y evaluar | Exporta, une las fuentes, aplica el split temporal con hueco, entrena el Pipeline y evalúa frente a la línea base ([regresion.md](regresion.md)) | Las fechas de cada conjunto y su n, los coeficientes (estandarizados y en unidades originales), el VIF, la tabla de métricas del modelo frente a la línea base y un recordatorio de las limitaciones de interpretación | `export` |
| 6 | Generar visualizaciones | Pregunta qué gráficas generar y si se muestran en ventana o se guardan como PNG | La lista de gráficas generadas y la ruta de cada PNG | `export` |
| 7 | Salir | Termina la aplicación; opcionalmente limpia `staging/` y `exchange/` | Un mensaje de despedida | — |

**Reglas comunes** [Recomendación]:

- Las opciones 3 a 6 avisan si la cobertura no es COMPLETA, pero no se bloquean: el usuario decide si continuar.
- Con la base vacía, las opciones 3 a 6 sugieren ejecutar primero la opción 2.
- Toda hora mostrada al usuario va en hora local de Medellín, con la UTC al lado cuando sea relevante (opción 3).

## Gráficas previstas

| Gráfica | Pregunta que responde | Datos necesarios |
|---|---|---|
| **Series temporales** (una por variable) | ¿Cómo evolucionaron la temperatura, la humedad, el viento y el PM2.5 durante el año? ¿Hay huecos o saltos raros? | Los registros de la ventana, en hora local; los huecos se dejan como cortes de la línea (sin unir los puntos) |
| **Perfil diurno** | ¿Cuál es el ciclo típico de cada variable a lo largo del día? ¿Coinciden las franjas con los momentos característicos? | La media por hora local (0–23) del **entrenamiento**, con una banda de dispersión y las franjas sombreadas |
| **Comparación por franjas** | ¿Difieren mañana, tarde y noche? | Los valores por franja y día (diagramas de caja), con el número de días válidos |
| **Dispersión de PM2.5 frente a cada predictora** | ¿Hay una relación visible? ¿Es aproximadamente lineal? | Las observaciones unidas (PM2.5 y predictora) del entrenamiento |
| **Matriz de correlación** | ¿Están correlacionadas las predictoras entre sí (multicolinealidad)? | Las 4 variables del entrenamiento |
| **Real frente a predicho** | ¿Cuánto se acerca el modelo? ¿Dónde falla? | Los valores reales y predichos de la prueba: un gráfico de dispersión con la diagonal y y = x, y la serie temporal superpuesta |
| **Residuos** | ¿Hay patrones que el modelo no captura (varianza no constante, autocorrelación)? | Residuos frente a predichos, residuos en el tiempo y un histograma de residuos |
| **Mapa de cobertura** | ¿Dónde están los huecos? | Una matriz de días × horas locales coloreada según el dato (presente, nulo o ausente), una por fuente |

Cada gráfica lleva título, ejes con unidades, el periodo y una nota de fuente («Datos: Open-Meteo.com (ERA5, CAMS)»), como exige la atribución ([fuentes-y-datos.md](fuentes-y-datos.md#licencia-y-atribución)).

## Ventana o PNG

| Modo | Cuándo conviene | Consideraciones |
|---|---|---|
| **Ventana interactiva** | Para explorar: hacer zoom en una serie o revisar un hueco | Necesita un entorno gráfico; el programa se detiene hasta cerrar la ventana |
| **PNG** | Para el informe, la presentación o equipos sin pantalla gráfica | Se guarda en `outputs/` con un nombre que incluye la gráfica y la fecha de generación, para no sobrescribir resultados anteriores [Recomendación] |

Si no hay entorno gráfico disponible, la aplicación debe guardar el PNG en lugar de fallar [Recomendación]. Cómo detectarlo con Matplotlib está [Por verificar, Fase 8].

## Experiencia de usuario en la terminal

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

- Las maquetas y los mensajes son ilustrativos; el texto final se ajusta en las fases 8 y 9.
- La lista de gráficas es la prevista; puede reducirse si alguna no aporta (por ejemplo, la matriz de correlación es redundante con el VIF).
- No se ha comprobado el comportamiento de Matplotlib sin pantalla gráfica en el equipo del estudiante (Fase 8).
- Se supone un único usuario y una sola ejecución a la vez.
