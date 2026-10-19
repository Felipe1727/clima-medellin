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
- **Resolución:** horaria, con **todas las horas** de PM2.5 (DP-02). La Fase 1 mostró que la API devuelve 24 valores al día que no son una interpolación simple de los pasos de 3 h ([fuentes-y-datos.md](fuentes-y-datos.md#hallazgos-de-la-fase-1)).
- **Tamaño esperado:** unas 8 700 observaciones por año (ERA5 termina en D−5, así que los últimos días no tienen predictoras), menos las excluidas.

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

- **Entrenamiento:** del inicio de la ventana a las 00:00 locales del mismo día **9 meses naturales** después (si ese día no existe, el último día del mes).
- **Hueco:** 24 h descartadas para que la autocorrelación de corto plazo no conecte el final del entrenamiento con el inicio de la prueba.
- **Prueba:** del final del hueco al fin de la ventana (~3 meses).
- Las fechas se fijan **por calendario**, no por número de observaciones, para que sean reproducibles; el resultado las imprime. Implementado en `split.temporal_split` (Fase 6) y usado por `regression.fit_and_evaluate` (Fase 7).

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
| Línea base | MAE_base | RMSE_base | ≈ 0 o negativo* |
| Regresión lineal | MAE_modelo | RMSE_modelo | R²_modelo |
| Mejora relativa | (MAE_base − MAE_modelo) / MAE_base | Ídem | Diferencia |

\* El R² de la línea base en prueba no es exactamente 0, porque usa la media del **entrenamiento** y no la de la prueba. Si las épocas difieren, será negativo.

Los valores reales con las muestras están en [Resultado con las muestras](#resultado-con-las-muestras).

## Diagnósticos

### Multicolinealidad (VIF)

- **Problema:** en Medellín, la temperatura y la humedad relativa probablemente estén muy correlacionadas de forma negativa, porque al calentarse el aire su humedad relativa baja [Supuesto]. Si dos predictoras cuentan casi la misma historia, el modelo no sabe a cuál atribuir el efecto, y los coeficientes individuales se vuelven inestables o con signos contraintuitivos, aunque las predicciones sigan siendo buenas.
- **Medida:** $\text{VIF}_j = \frac{1}{1 - R^2_j}$, donde $R^2_j$ es el R² de la regresión de la predictora $j$ sobre las demás. VIF = 1 indica ninguna colinealidad; > 5–10 es preocupante [Supuesto: umbral convencional].
- **Qué hacer:** informar del VIF junto a los coeficientes y no interpretar individualmente los coeficientes con un VIF alto. No se compara con modelos alternativos sin alguna variable: la selección de variables queda fuera del alcance (Fase 7).

### Autocorrelación

- **Problema:** los residuos de horas consecutivas probablemente están correlacionados. Las predicciones siguen siendo válidas, pero los errores estándar y los p-valores clásicos subestiman la incertidumbre (hay menos información independiente de la que parece).
- **Diagnóstico:** el gráfico de residuos en el tiempo y la autocorrelación de los residuos a 1 paso. El estadístico de Durbin-Watson es una opción [Recomendación].
- **Consecuencia práctica:** no se presentan p-valores como prueba de significación sin advertirlo. El split temporal con hueco (ya adoptado) evita la parte más grave del problema: las métricas optimistas.

### Asimetría de PM2.5

- **Problema:** PM2.5 tiene una distribución asimétrica a la derecha: muchos valores moderados y algunos picos altos (en la muestra anual, mediana 10,6 µg/m³, media 12,9, percentil 95 de 29,3 y máximo de 49,9). La regresión lineal por mínimos cuadrados da mucho peso a los picos.
- **Diagnóstico:** el histograma de PM2.5 y el gráfico de residuos frente a predichos (si los residuos se abren en abanico, la varianza no es constante).
- **Opción descartada:** modelar log(PM2.5). Cambiaría la interpretación de los coeficientes (efectos porcentuales) y complicaría comparar las métricas. **Decisión (DP-08): escala original**, más fácil de explicar; la asimetría se muestra en el histograma y en los residuos.

## Limitaciones de interpretación

1. **Se modela un modelo.** Tanto PM2.5 (CAMS) como la meteorología (ERA5) son productos de modelos, no mediciones ([fuentes-y-datos.md](fuentes-y-datos.md#modelados-frente-a-observados)). CAMS se ejecuta con el IFS del ECMWF, que calcula su propia meteorología [Verificado: Fase 1], así que la regresión puede estar recuperando en parte **las ecuaciones internas de CAMS** y no la relación real en Medellín. Un R² alto no demostraría que «el viento limpia el aire de Medellín».
2. **Correlación no implica causalidad.** La temperatura y el PM2.5 pueden variar juntos porque ambos siguen el ciclo diario (sol, tráfico, capa de mezcla), no porque uno cause el otro. El tráfico de la hora punta, ausente del modelo, es un factor de confusión evidente.
3. **Escala espacial.** Las relaciones corresponden a celdas de 25–45 km, no al centro de Medellín.
4. **Escala temporal.** Un año de datos y una prueba de ~3 meses no permiten generalizar a otros años ni a eventos extremos (por ejemplo, episodios de incendios regionales).
5. **Extrapolación.** El modelo no es fiable fuera del rango de valores visto en el entrenamiento.
6. **Empalmes del pronóstico.** El PM2.5 de CAMS salta a las 00 y 12 UTC porque el archivo encadena pronósticos ([fuentes-y-datos.md](fuentes-y-datos.md#empalmes-de-las-ejecuciones-del-pronóstico-00-y-12-utc)). Esos saltos no tienen relación con la meteorología y aumentan el error del modelo; no se corrigen.

## Resultado con las muestras

Resultado de `fit_and_evaluate` con las muestras de `samples/` (descargadas el 2026-10-18) y la ventana de D = 2026-10-18. Es reproducible: la misma ejecución da los mismos números (prueba `test_results_are_reproducible`).

**Datos y separación:** 8 755 horas en la ventana, de las que 8 659 tienen las cuatro variables (se excluyen 96: los últimos 4 días, sin ERA5). Entrenamiento: 2025-10-18 → 2026-07-18 (6 552 horas). Hueco de 24 h. Prueba: 2026-07-19 → 2026-10-14 (2 083 horas; ERA5 termina en D−5). Fechas a las 00:00 locales.

**Métricas en la prueba:**

| | MAE (µg/m³) | RMSE (µg/m³) | R² |
|---|---|---|---|
| Línea base (media de entrenamiento = 13,97 µg/m³) | 6,10 | 7,01 | −0,66 |
| Regresión lineal | 5,72 | 7,03 | −0,67 |
| Mejora relativa | 6,2 % | −0,3 % | −0,01 |

**Coeficientes** (intercepto estandarizado 13,97 µg/m³ = línea base; intercepto en unidades originales −41,5 µg/m³):

| Predictora | Estandarizado (µg/m³ por desviación) | Original | VIF |
|---|---|---|---|
| Temperatura | +2,43 | +1,03 µg/m³ por °C | 3,64 |
| Humedad relativa | +3,99 | +0,42 µg/m³ por punto de % | 4,11 |
| Viento | −0,99 | −2,19 µg/m³ por m/s | 1,34 |

**Durbin-Watson de los residuos de prueba:** 0,14.

**Interpretación:**

- **El modelo apenas aporta capacidad predictiva.** Reduce el MAE un 6 % frente a la línea base, pero su RMSE es ligeramente peor: acierta algo mejor en las horas típicas y se equivoca igual o más en los picos.
- **Los dos R² son negativos** porque la prueba (julio–octubre) tiene una media de PM2.5 de 9,6 µg/m³, muy por debajo de la media del entrenamiento (14,0). Predecir con la media del entrenamiento es peor que predecir con la media de la propia prueba, y el modelo no corrige ese cambio de época: es la limitación de la [separación temporal](#separación-temporal-con-hueco) con una prueba de una sola estación.
- **El viento** tiene el signo esperado: más viento se asocia con menos PM2.5.
- **La temperatura tiene un coeficiente positivo**, contra la intuición de la capa de mezcla. Su VIF (3,6) y el de la humedad (4,1) indican una colinealidad moderada entre ambas, y las dos siguen el ciclo diario junto con los empalmes de CAMS (el PM2.5 sube a las 19 h locales, cuando la temperatura de ERA5 todavía está alta, ver [cobertura-y-franjas.md](cobertura-y-franjas.md#resultado-con-las-muestras-de-la-fase-1)). No se debe concluir que el calor aumenta el PM2.5.
- **Durbin-Watson = 0,14** indica una autocorrelación muy fuerte de los residuos: hay mucha menos información independiente de la que sugieren 6 552 horas. Por eso no se presentan p-valores.

Formulación para la defensa con estos números: «En los datos modelados de ERA5 y CAMS para la celda de Medellín, entre el 2025-10-18 y el 2026-10-14, el modelo lineal con temperatura, humedad y viento no explica la variabilidad de PM2.5 en la prueba mejor que su media (R² negativo, igual que la línea base, por el cambio de estación) y reduce el MAE solo un 6 % frente a la línea base. Esto describe una asociación débil en los modelos, no un efecto causal ni una validación con mediciones».

Al ejecutar la aplicación con datos más recientes, los números cambiarán (la ventana es móvil, D-016); la estructura de la interpretación sigue siendo válida.

Formulación recomendada para la defensa: «En los datos modelados de ERA5 y CAMS para la celda de Medellín, durante [periodo], el modelo lineal con temperatura, humedad y viento explica X % de la variabilidad de PM2.5 en la prueba y reduce el MAE un Y % frente a la línea base. Esto describe una asociación en los modelos, no un efecto causal ni una validación con mediciones».

## Preguntas de comprobación

1. ¿Por qué un split aleatorio daría un R² más alto que el split temporal, y por qué ese R² sería engañoso?
2. Si se ajustara el escalador con todo el año en lugar de solo con el entrenamiento, ¿qué información del periodo de prueba se filtraría al modelo?
3. El modelo obtiene un R² de 0,35 en prueba y la línea base un MAE de 6 µg/m³ frente a 5,2 del modelo. ¿Cómo describirías el resultado y qué dirías del valor práctico del modelo? *(Valores ficticios.)*
4. La temperatura tiene un VIF de 9 y su coeficiente es positivo, contra lo esperado. ¿Qué podría estar pasando y por qué no se debe concluir que el calor aumenta el PM2.5?

## Limitaciones y supuestos

- Los ejemplos numéricos de las secciones teóricas son ficticios; los resultados reales con las muestras están en [Resultado con las muestras](#resultado-con-las-muestras).
- La intuición física (capa de mezcla, viento) es conocimiento general y no se ha verificado con fuentes en este proyecto.
- PM2.5 se usa con resolución horaria (DP-02); los empalmes del pronóstico a las 00 y 12 UTC añaden saltos que la meteorología no explica.
- Los umbrales del VIF y la elección de Durbin-Watson son convenciones, no requisitos.
- La separación se fija por calendario (9 meses naturales, 24 h de hueco y el resto como prueba).
