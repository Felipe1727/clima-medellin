# Glosario

Definiciones breves de los términos que se usan en la documentación del proyecto. Cuando aplica, el término original en inglés va entre paréntesis. Cada definición dice qué es el concepto y para qué sirve en este proyecto; el desarrollo completo está en el documento enlazado.

## Datos y fuentes

| Término | Definición |
|---|---|
| **API** (*Application Programming Interface*) | Interfaz para que un programa pida datos a otro. Aquí son servicios web de Open-Meteo que reciben una URL con parámetros (coordenadas, fechas, variables) y responden con JSON. |
| **JSON** (*JavaScript Object Notation*) | Formato de texto para datos estructurados con objetos `{clave: valor}`, listas, números, cadenas, `true`/`false` y `null`. Lo usan las APIs y las respuestas pequeñas entre Java y Python. |
| **JSON Lines** (*JSON Lines*, `.jsonl`) | Archivo de texto en el que **cada línea es un objeto JSON completo**. Permite leer y escribir registro a registro y localizar la línea exacta de un error. Es el formato de los lotes de `staging/` y `exchange/` ([arquitectura.md](arquitectura.md#protocolo-de-comunicación)). |
| **Reanálisis** (*reanalysis*) | Reconstrucción del estado pasado de la atmósfera que combina un modelo numérico con observaciones históricas de todo el mundo. No es una medición directa en un punto, pero es físicamente coherente y no tiene huecos. |
| **ERA5** | Reanálisis global del ECMWF (Centro Europeo de Previsiones Meteorológicas a Medio Plazo) dentro del programa Copernicus. En Open-Meteo: 0,25° (~25 km), horario, desde 1940, con 5 días de retraso. Fuente meteorológica del proyecto ([fuentes-y-datos.md](fuentes-y-datos.md)). |
| **CAMS** (*Copernicus Atmosphere Monitoring Service*) | Servicio europeo de Copernicus que modela la composición atmosférica (aerosoles, gases). Produce los pronósticos de PM2.5 que entrega Open-Meteo. |
| **PM2.5** (*particulate matter ≤ 2.5 µm*) | Partículas en suspensión de diámetro igual o menor a 2,5 micrómetros, medidas en µg/m³. Penetran en los pulmones y son un indicador clave de calidad del aire. **En este proyecto es un valor modelado por CAMS, no medido.** |
| **Resolución espacial** (*spatial resolution*) | Tamaño de la celda de la malla del modelo. Con 25 km, todo lo que está dentro de la celda (montañas y valle) se resume en un solo valor. |
| **Resolución temporal** (*temporal resolution*) | Intervalo entre dos valores consecutivos: 1 hora en ERA5 y 3 horas en el dominio global de CAMS. |
| **Capa de mezcla** (*mixing layer / boundary layer*) | Capa de aire cercana al suelo donde los contaminantes se mezclan. En la madrugada suele ser baja y estable, y atrapa las partículas en un valle como el de Aburrá; con el calentamiento del día crece y las dispersa. Es el mecanismo físico que explica la relación entre temperatura, viento y PM2.5, aunque no es una variable del modelo. |

## Tiempo y cobertura

| Término | Definición |
|---|---|
| **UTC** (*Coordinated Universal Time*) | Hora de referencia mundial, sin horario de verano. Todas las marcas de tiempo se almacenan en UTC (D-008). |
| **Zona horaria** (*time zone*) | Regla que convierte UTC en hora local. Se usa `America/Bogota`, que es UTC−5 sin horario de verano ([Por verificar en la Fase 3]). Ejemplo: 13:00 UTC equivale a las 8:00 en Medellín. |
| **Cobertura temporal** (*temporal coverage*) | Proporción de pasos esperados que tienen un valor no nulo en un periodo. Por ejemplo, 8 700 de 8 760 horas equivalen a un 99,3 % ([cobertura-y-franjas.md](cobertura-y-franjas.md#criterio-de-cobertura)). |
| **Hueco** (*gap*) | Secuencia continua de pasos esperados sin valor. Un hueco de 6 h en la temperatura, entre las 10:00 y las 15:59 locales, borra justo el máximo diario. |
| **Perfil diurno** (*diurnal profile*) | Valor medio de una variable para cada hora local del día (0–23), calculado sobre muchos días. Muestra el ciclo típico; por ejemplo, el mínimo de temperatura al amanecer. |
| **Franja horaria** | Resumen de una variable en una ventana local de 3 horas (mañana 7–9 h, tarde 13–15 h, noche 19–21 h). Se calcula y no se guarda (D-009, D-021). |

## Persistencia

| Término | Definición |
|---|---|
| **ObjectDB** | Base de datos orientada a objetos para Java, que guarda las entidades en un archivo (`.odb`) y se usa mediante JPA. Su versión gratuita admite hasta 10 clases de entidad y un millón de entidades por archivo ([Verificado: ObjectDB](https://www.objectdb.com/database/purchase)). |
| **JPA** (*Jakarta / Java Persistence API*) | Estándar de Java para guardar y consultar objetos (entidades) en una base de datos mediante anotaciones y un `EntityManager`. ObjectDB lo implementa. |
| **Entidad** (*entity*) | Clase Java cuyas instancias se guardan en la base: Location, WeatherRecord, AirQualityRecord e IngestionBatch. |
| **Transacción** (*transaction*) | Grupo de operaciones que se aplican todas o ninguna (*commit* o *rollback*). Garantiza que un lote no quede guardado a medias. |
| **Clave natural** (*natural key*) | Combinación de atributos con significado propio que identifica un registro de forma única. Aquí: ubicación + fuente + timestamp UTC (D-011). Se distingue del identificador técnico autogenerado. |
| **Duplicado** (*duplicate*) | Registro con la misma clave natural que otro ya guardado. Se detecta y se omite, sin sobrescribir (D-013). |
| **null** | Ausencia de valor. Es distinto de 0: «no se sabe la temperatura» no equivale a «hace 0 °C» (D-012). En Pandas aparece como NaN. |
| **Lote de ingesta** (*ingestion batch*) | Una descarga concreta, con su fuente, periodo pedido, fecha y conteos. Se registra en la entidad IngestionBatch para conocer la procedencia de cada dato. |

## Análisis

| Término | Definición |
|---|---|
| **DataFrame** | Tabla en memoria de Pandas, con columnas tipadas y un índice (aquí, el tiempo). Es la estructura central del procesamiento en Python. |
| **Pipeline** | Objeto de scikit-learn que encadena pasos (escalar y luego ajustar la regresión) y garantiza que todos se ajusten solo con los datos de entrenamiento ([regresion.md](regresion.md#pipeline-y-prevención-de-fuga-de-información)). |
| **Fuga de información** (*data leakage*) | Uso, durante el entrenamiento, de información que no estaría disponible al predecir (por ejemplo, la media del conjunto de prueba). Produce métricas engañosamente buenas. |
| **Split temporal** (*temporal split*) | División de los datos en entrenamiento y prueba según el tiempo: el pasado para entrenar y el futuro para evaluar. |
| **Línea base** (*baseline*) | Predictor trivial que sirve de referencia; aquí, predecir siempre la media de PM2.5 del entrenamiento. Un modelo útil debe superarla. |
| **MAE** (*Mean Absolute Error*) | Error absoluto medio, en µg/m³: cuánto se equivoca el modelo en promedio. |
| **RMSE** (*Root Mean Squared Error*) | Raíz del error cuadrático medio, en µg/m³. Penaliza más los errores grandes que el MAE. |
| **R²** (coeficiente de determinación) | Proporción de la variabilidad de PM2.5 explicada por el modelo. 1 es perfecto; 0 equivale a predecir la media; en prueba puede ser negativo. |
| **Multicolinealidad** (*multicollinearity*) | Correlación fuerte entre predictoras (por ejemplo, temperatura y humedad), que vuelve inestables e ininterpretables los coeficientes individuales. |
| **VIF** (*Variance Inflation Factor*) | Medida de la multicolinealidad de cada predictora: VIF = 1 / (1 − R²ⱼ), donde R²ⱼ mide cuánto explican las demás predictoras a la predictora j. Valores > 5–10 suelen considerarse preocupantes [Supuesto: umbral convencional]. |
| **Autocorrelación** (*autocorrelation*) | Correlación de una serie consigo misma desplazada en el tiempo: el PM2.5 de las 8:00 se parece al de las 7:00. Hace que los datos horarios no sean independientes. |

## Limitaciones y supuestos

- Las definiciones están simplificadas a propósito y priorizan la intuición; el tratamiento riguroso está en el documento enlazado en cada caso.
- Los valores numéricos de resolución y latencia citados aquí resumen [fuentes-y-datos.md](fuentes-y-datos.md), que es donde se verifican.
- El umbral del VIF (5–10) es una convención habitual, no una regla estricta.
