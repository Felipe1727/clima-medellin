# Regresión lineal

Este documento explica el modelo estadístico del proyecto: qué se quiere estimar, por qué con una regresión lineal, cómo se entrena y se evalúa sin hacer trampa, y, sobre todo, **qué se puede y qué no se puede concluir** de sus resultados. Está escrito para que el estudiante pueda explicar cada paso en la defensa oral. Las decisiones que se apoyan en este documento son D-017 a D-020 ([decisiones.md](decisiones.md)).

## Objetivo del modelo

**Pregunta:** ¿en qué medida las condiciones meteorológicas (temperatura, humedad relativa y viento) permiten estimar el PM2.5 en Medellín, según los modelos ERA5 y CAMS?

- **Variable objetivo (y):** PM2.5 en µg/m³.
- **Predictoras (X):** temperatura a 2 m (°C), humedad relativa a 2 m (%) y velocidad del viento a 10 m (m/s).

**Intuición física** [Supuesto: conocimiento general de meteorología urbana; no verificado con fuentes en este proyecto]:

- En las madrugadas, el aire cerca del suelo es frío y estable, la **capa de mezcla** es baja y las partículas se acumulan en el valle.
- Al calentarse el día, la capa crece y las partículas se diluyen.
- Más viento suele dispersar.

Por eso se espera que la temperatura y el viento tengan relación negativa con PM2.5. Que el modelo lo confirme o no forma parte del análisis.

## Por qué una regresión lineal

| Razón | Explicación |
|---|---|
| Interpretable | Cada coeficiente dice cuánto cambia la predicción por unidad (o por desviación estándar) de una predictora, manteniendo fijas las demás. |
| Línea de referencia | Es el modelo más simple que usa las predictoras; cualquier modelo más complejo debería compararse con él. |
| Adecuada al curso | El objetivo es comprender todo el flujo de datos, no maximizar la precisión. |
| Pocas predictoras | Con 3 variables no hay riesgo de sobreajuste por exceso de parámetros. |

**Lo que no hace:** no captura relaciones no lineales (por ejemplo, el efecto del viento podría saturarse), interacciones (el viento podría importar más de noche) ni la dinámica temporal (el PM2.5 de ahora depende del de hace una hora). Son limitaciones asumidas (D-017).

## Mínimos cuadrados

### Intuición

Hay una nube de puntos: cada hora es un punto con su temperatura, humedad, viento y PM2.5. Se busca el «plano» (con 3 predictoras, un hiperplano) que pase lo más cerca posible de todos los puntos. «Lo más cerca» significa: que la **suma de los errores al cuadrado** sea mínima.

¿Por qué al cuadrado? Porque así los errores positivos y negativos no se cancelan, los errores grandes se penalizan más y la solución puede calcularse de forma exacta.

### Formulación

El modelo predice:

$$\hat{y}_i = \beta_0 + \beta_1 \, T_i + \beta_2 \, HR_i + \beta_3 \, V_i$$

donde, para la hora $i$, $\hat{y}_i$ es el PM2.5 predicho, $T_i$ la temperatura, $HR_i$ la humedad y $V_i$ el viento; $\beta_0$ es el intercepto y $\beta_1, \beta_2, \beta_3$ los coeficientes.

Los coeficientes se eligen para minimizar:

$$\text{SSE}(\beta) = \sum_{i=1}^{n} \left( y_i - \hat{y}_i \right)^2$$

**En palabras:** para cada hora, se resta la predicción del valor real (el residuo), se eleva al cuadrado y se suma sobre todas las horas. Los mejores coeficientes son los que hacen esa suma lo más pequeña posible.

La solución cerrada en forma matricial es $\hat{\beta} = (X^\top X)^{-1} X^\top y$. **En palabras:** el método combina cómo varían las predictoras entre sí ($X^\top X$) con cómo varían junto con PM2.5 ($X^\top y$). Si dos predictoras son casi idénticas, $X^\top X$ es casi singular y los coeficientes se vuelven inestables. Esa es la razón matemática del problema de la multicolinealidad (ver [Diagnósticos](#diagnósticos)).

## Interpretación del intercepto y de los coeficientes

Como el Pipeline estandariza las predictoras (media 0 y desviación 1 en entrenamiento):

- **Intercepto ($\beta_0$):** la predicción cuando todas las predictoras están en su media de entrenamiento. Con predictoras estandarizadas, coincide con la **media de PM2.5 del entrenamiento**, es decir, con la línea base.
- **Coeficiente ($\beta_j$):** cuántos µg/m³ cambia la predicción de PM2.5 cuando la predictora $j$ aumenta **una desviación estándar**, **manteniendo constantes las demás**. Permite comparar la importancia relativa de las predictoras porque todas están en la misma escala.
- Para expresarlo en unidades originales (por ejemplo, «por cada °C»), se divide el coeficiente entre la desviación estándar de la predictora en entrenamiento.

Ejemplo **ficticio** de lectura: si $\beta_{V} = -2{,}1$ y la desviación del viento es 1,3 m/s, la lectura sería: «manteniendo fijas la temperatura y la humedad, 1,3 m/s más de viento se asocia con 2,1 µg/m³ menos de PM2.5 en el modelo». La palabra clave es **se asocia**; no significa «causa» (ver [Limitaciones de interpretación](#limitaciones-de-interpretación)).

## Conjunto de datos

- **Unidad de observación:** un timestamp con PM2.5 y las 3 predictoras no nulas. Las filas con algún `null` se excluyen, sin imputar, y se informa cuántas se excluyeron.
- **Unión de las fuentes:** WeatherRecord y AirQualityRecord se unen por timestamp UTC en Python, después de la exportación.
- **Resolución:** [Pendiente de revisión, D-006 y DP-02] si PM2.5 tiene un paso nativo de 3 h:
  - Si la API devuelve valores interpolados cada hora, usarlos todos triplicaría artificialmente el tamaño de la muestra y aumentaría la autocorrelación. [Recomendación] Usar solo los timestamps nativos (unos 2 920 por año).
  - Si la API devuelve `null` entre pasos, el filtrado anterior lo hace automáticamente.
- **Tamaño esperado:** entre ~2 900 (paso de 3 h) y ~8 700 (horario) observaciones por año, menos las excluidas [Supuesto].

## Separación temporal con hueco

### Por qué no un split aleatorio

Los datos horarios están **autocorrelacionados**: el PM2.5 de las 08:00 se parece mucho al de las 07:00. Con un split aleatorio, la hora 07:00 podría quedar en entrenamiento y la 08:00 en prueba. El modelo «vería» casi la respuesta y las métricas serían optimistas. Eso no simula la situación real, en la que se predice un periodo nunca visto.

### Esquema (D-018)

```text
 inicio de la ventana                                            fin efectivo
 |──────────── entrenamiento (~9 meses) ────────────|·24 h·|── prueba (~3 meses) ──|
                                                     hueco
                                                   (se descarta)
```

- **Entrenamiento:** las primeras ~3/4 partes del periodo, por fecha.
- **Hueco:** 24 h descartadas para que la autocorrelación de corto plazo no conecte el final del entrenamiento con el inicio de la prueba.
- **Prueba:** el último ~1/4 del periodo.
- Las proporciones exactas (por fechas o por número de observaciones) se fijan en la Fase 7 [Recomendación: por fechas, para que sean reproducibles].

**Limitación:** la prueba cubre unos 3 meses concretos (por ejemplo, de julio a octubre), con un régimen de lluvias y de emisiones que puede diferir del entrenamiento. Las métricas reflejan cómo generaliza el modelo **a esa época**, no al año en general.

## Pipeline y prevención de fuga de información

**Fuga de información:** usar, al entrenar, algo que no se conocería al predecir. Ejemplo: estandarizar con la media y la desviación de **todo** el año. La media incluiría los 3 meses de prueba, así que el modelo «sabría» algo del futuro.

**Solución (D-019):** un Pipeline de scikit-learn con dos pasos:

1. Escalador (estandarización): aprende la media y la desviación **solo con el entrenamiento**.
2. Regresión lineal: se ajusta con los datos de entrenamiento ya escalados.

Al evaluar, el Pipeline aplica a la prueba la **misma** transformación aprendida en entrenamiento, sin volver a calcular nada. Lo mismo vale para cualquier decisión derivada de los datos: el perfil diurno, la elección de franjas o el umbral de valores atípicos se calculan con el entrenamiento (ver [cobertura-y-franjas.md](cobertura-y-franjas.md#perfil-diurno)).

## Métricas

Notación: $y_i$ real, $\hat{y}_i$ predicho, $n$ observaciones de prueba, $\bar{y}$ media de la prueba.

| Métrica | Fórmula | Intuición | Unidades | Cuándo usarla |
|---|---|---|---|---|
| **MAE** | $\frac{1}{n}\sum \lvert y_i - \hat{y}_i \rvert$ | «En promedio, me equivoco en X µg/m³» | µg/m³ | Para comunicar el error típico; es robusta frente a valores extremos |
| **RMSE** | $\sqrt{\frac{1}{n}\sum (y_i - \hat{y}_i)^2}$ | Como el MAE, pero los errores grandes pesan más | µg/m³ | Cuando equivocarse mucho en un pico es especialmente grave |
| **R²** | $1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$ | Proporción de la variabilidad explicada | Sin unidades | Para comparar con «predecir la media»; en prueba **puede ser negativo** si el modelo es peor que la media de la prueba |

**Relación útil:** siempre RMSE ≥ MAE. Si el RMSE es mucho mayor que el MAE, hay unos pocos errores muy grandes, típicamente en los picos de contaminación.

## Línea base

**Definición (D-020):** predecir siempre la **media de PM2.5 del entrenamiento**, sin mirar ninguna predictora.

**Por qué:** responde a «¿sirven para algo las variables meteorológicas?». Un MAE de 4 µg/m³ no dice nada por sí solo; dice mucho si la línea base tiene un MAE de 4,1 (casi nada ganado) o de 9 (mejora grande).

**Cómo comparar:**

| | MAE | RMSE | R² |
|---|---|---|---|
| Línea base | — | — | ≈ 0 o negativo* |
| Regresión lineal | — | — | — |
| Mejora relativa | (MAE_base − MAE_modelo) / MAE_base | Ídem | Diferencia |

\* El R² de la línea base en prueba no es exactamente 0, porque usa la media del **entrenamiento** y no la de la prueba. Si las épocas difieren, será negativo.

La tabla se llenará en la Fase 7; no hay resultados todavía.

## Diagnósticos

### Multicolinealidad (VIF)

- **Problema:** en Medellín, la temperatura y la humedad relativa probablemente estén muy correlacionadas de forma negativa, porque al calentarse el aire su humedad relativa baja [Supuesto]. Si dos predictoras cuentan casi la misma historia, el modelo no sabe a cuál atribuir el efecto, y los coeficientes individuales se vuelven inestables o con signos contraintuitivos, aunque las predicciones sigan siendo buenas.
- **Medida:** $\text{VIF}_j = \frac{1}{1 - R^2_j}$, donde $R^2_j$ es el R² de la regresión de la predictora $j$ sobre las demás. VIF = 1 indica ninguna colinealidad; > 5–10 es preocupante [Supuesto: umbral convencional].
- **Qué hacer:** informar del VIF junto a los coeficientes y no interpretar individualmente los coeficientes con un VIF alto. Opcionalmente, comparar con un modelo sin una de las dos variables (decisión de la Fase 7).

### Autocorrelación

- **Problema:** los residuos de horas consecutivas probablemente están correlacionados. Las predicciones siguen siendo válidas, pero los errores estándar y los p-valores clásicos subestiman la incertidumbre (hay menos información independiente de la que parece).
- **Diagnóstico:** el gráfico de residuos en el tiempo y la autocorrelación de los residuos a 1 paso. El estadístico de Durbin-Watson es una opción [Recomendación].
- **Consecuencia práctica:** no se presentan p-valores como prueba de significación sin advertirlo. El split temporal con hueco (ya adoptado) evita la parte más grave del problema: las métricas optimistas.

### Asimetría de PM2.5

- **Problema:** PM2.5 suele tener una distribución asimétrica a la derecha: muchos valores moderados y algunos picos altos [Supuesto, se comprobará con el histograma de la Fase 6]. La regresión lineal por mínimos cuadrados da mucho peso a los picos.
- **Diagnóstico:** el histograma de PM2.5 y el gráfico de residuos frente a predichos (si los residuos se abren en abanico, la varianza no es constante).
- **Opción:** modelar log(PM2.5). Cambia la interpretación de los coeficientes (efectos porcentuales) y complica comparar las métricas. Decisión de la Fase 7 (DP-08); por defecto se usa la escala original, porque es más fácil de explicar [Recomendación].

## Limitaciones de interpretación

1. **Se modela un modelo.** Tanto PM2.5 (CAMS) como la meteorología (ERA5) son productos de modelos, no mediciones ([fuentes-y-datos.md](fuentes-y-datos.md#modelados-frente-a-observados)). Si CAMS usa meteorología del mismo centro (ECMWF) [Por verificar, Fase 1], la regresión puede estar recuperando en parte **las ecuaciones internas de CAMS** y no la relación real en Medellín. Un R² alto no demostraría que «el viento limpia el aire de Medellín».
2. **Correlación no implica causalidad.** La temperatura y el PM2.5 pueden variar juntos porque ambos siguen el ciclo diario (sol, tráfico, capa de mezcla), no porque uno cause el otro. El tráfico de la hora punta, ausente del modelo, es un factor de confusión evidente.
3. **Escala espacial.** Las relaciones corresponden a celdas de 25–45 km, no al centro de Medellín.
4. **Escala temporal.** Un año de datos y una prueba de ~3 meses no permiten generalizar a otros años ni a eventos extremos (por ejemplo, episodios de incendios regionales).
5. **Extrapolación.** El modelo no es fiable fuera del rango de valores visto en el entrenamiento.

Formulación recomendada para la defensa: «En los datos modelados de ERA5 y CAMS para la celda de Medellín, durante [periodo], el modelo lineal con temperatura, humedad y viento explica X % de la variabilidad de PM2.5 en la prueba y reduce el MAE un Y % frente a la línea base. Esto describe una asociación en los modelos, no un efecto causal ni una validación con mediciones».

## Preguntas de comprobación

1. ¿Por qué un split aleatorio daría un R² más alto que el split temporal, y por qué ese R² sería engañoso?
2. Si se ajustara el escalador con todo el año en lugar de solo con el entrenamiento, ¿qué información del periodo de prueba se filtraría al modelo?
3. El modelo obtiene un R² de 0,35 en prueba y la línea base un MAE de 6 µg/m³ frente a 5,2 del modelo. ¿Cómo describirías el resultado y qué dirías del valor práctico del modelo? *(Valores ficticios.)*
4. La temperatura tiene un VIF de 9 y su coeficiente es positivo, contra lo esperado. ¿Qué podría estar pasando y por qué no se debe concluir que el calor aumenta el PM2.5?

## Limitaciones y supuestos

- No hay todavía datos ni resultados; todos los ejemplos numéricos son ficticios.
- La intuición física (capa de mezcla, viento) es conocimiento general y no se ha verificado con fuentes en este proyecto.
- El tratamiento de la resolución de PM2.5 depende de la verificación de la Fase 1 (DP-02).
- Los umbrales del VIF y la elección de Durbin-Watson son convenciones, no requisitos.
- Las proporciones del split (9 + 3 meses) son aproximadas y se fijan en la Fase 7.
