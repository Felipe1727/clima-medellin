# Registro de decisiones

Este documento reúne las decisiones de diseño del proyecto en un formato ligero, inspirado en los ADR (*Architecture Decision Records*). Cada entrada explica el problema, las opciones consideradas, lo que se decidió y lo que implica. El objetivo es que el estudiante pueda defender cada decisión con sus propias palabras y saber cuáles siguen abiertas. Los demás documentos remiten aquí mediante el identificador `D-xxx`.

**Estados posibles:**

- **Definitiva:** no se espera cambiarla. Revisarla requeriría una razón nueva y seria.
- **Provisional:** es una hipótesis de trabajo razonable que se confirmará con datos o pruebas en una fase concreta.
- **Pendiente de revisión:** durante la documentación apareció un motivo serio para cuestionarla. Se mantiene hasta que se revise, pero no conviene construir sobre ella sin resolver antes la duda.

**Etiquetas de rigor** (usadas en todos los documentos): [Verificado: fuente], [Supuesto], [Recomendación] y [Por verificar].

## Resumen

| ID | Decisión | Estado | Se revisa en |
|---|---|---|---|
| [D-001](#d-001--python-orquesta-la-cli) | Python orquesta la CLI de 7 opciones | Definitiva | — |
| [D-002](#d-002--java-es-el-único-que-accede-a-objectdb) | Java es el único que abre ObjectDB | Definitiva | — |
| [D-003](#d-003--comunicación-entre-procesos-mediante-un-jar-con-subcomandos) | Comunicación por procesos: JAR con subcomandos | Definitiva | Fase 4 (detalles) |
| [D-004](#d-004--intercambio-de-lotes-en-json-lines-y-reglas-de-stdoutstderr) | Lotes en JSON Lines; stdout solo JSON; logs en stderr | Definitiva | Fase 4 (detalles) |
| [D-005](#d-005--meteorología-open-meteo-historical-con-era5-explícito) | Meteorología: ERA5 explícito | Provisional | Fase 1 |
| [D-006](#d-006--calidad-del-aire-pm25-de-cams-global-vía-open-meteo) | PM2.5 de CAMS global (modelo) | **Pendiente de revisión** | Fase 1 |
| [D-007](#d-007--un-único-punto-representativo-de-medellín) | Un único punto representativo | Provisional | Fase 1 |
| [D-008](#d-008--almacenar-en-utc-calcular-en-americabogota) | UTC para almacenar; America/Bogota para calcular | Definitiva | — |
| [D-009](#d-009--franjas-horarias-mañana-tarde-y-noche) | Franjas 7–9, 13–15 y 19–21 h, con un mínimo de 2 de 3 horas | **Pendiente de revisión** | Fases 1 y 6 |
| [D-010](#d-010--cuatro-entidades-en-objectdb) | Cuatro entidades en ObjectDB | Provisional | Fase 2 |
| [D-011](#d-011--clave-natural-ubicación--fuente--timestamp-utc) | Clave natural: ubicación + fuente + timestamp UTC | Definitiva | Fase 2 (implementación) |
| [D-012](#d-012--ausentes-como-null-nunca-como-0) | Ausentes como null, nunca 0 | Definitiva | — |
| [D-013](#d-013--solo-inserciones-correcciones-mediante-lote-explícito) | Solo inserciones; correcciones mediante un lote explícito | Provisional | Fase 2 |
| [D-014](#d-014--criterio-de-cobertura-98--y-hueco-máximo-de-6-h) | Cobertura COMPLETA: ≥ 98 % y hueco ≤ 6 h | Provisional | Fase 5 |
| [D-015](#d-015--actualización-incremental-respetando-la-latencia) | Actualización incremental respetando la latencia | Definitiva | Fase 5 (detalles) |
| [D-016](#d-016--ventana-móvil-de-un-año) | Ventana móvil de un año | Definitiva | Fase 5 (caso del 29 de febrero) |
| [D-017](#d-017--regresión-lineal-pm25--temperatura--humedad--viento) | Regresión lineal: PM2.5 ~ temperatura + humedad + viento | Definitiva | — |
| [D-018](#d-018--split-temporal-9--3-meses-con-hueco-de-24-h) | Split temporal de unos 9 + 3 meses con hueco de 24 h | Provisional | Fase 7 |
| [D-019](#d-019--pipeline-con-escalador-ajustado-solo-con-entrenamiento) | Pipeline con escalador ajustado solo con entrenamiento | Definitiva | — |
| [D-020](#d-020--línea-base-y-métricas) | Línea base = media del entrenamiento; MAE, RMSE y R² | Definitiva | — |
| [D-021](#d-021--las-franjas-se-calculan-y-no-se-persisten) | Las franjas se calculan y no se persisten | Definitiva | — |
| [D-022](#d-022--unidades-canónicas) | Unidades canónicas (°C, %, m/s, µg/m³) | Provisional | Fase 3 |
| [D-023](#d-023--visualizaciones-con-matplotlib-en-ventana-o-png) | Matplotlib, con salida en ventana o PNG | Provisional | Fase 8 |

Las decisiones D-001 a D-021 vienen del encargo inicial (sección 2). D-022 y D-023 se añaden aquí porque se derivan de ellas y conviene dejarlas por escrito; ambas son provisionales.

---

## D-001 — Python orquesta la CLI

- **Contexto:** el usuario interactúa con una sola aplicación de terminal. La descarga, la limpieza, la estadística y las gráficas dependen del ecosistema de Python (Pandas, scikit-learn, Matplotlib).
- **Opciones consideradas:** (a) Python como orquestador que llama a Java; (b) Java como orquestador que llama a Python; (c) dos programas independientes que el usuario ejecuta por separado.
- **Decisión:** (a). Python presenta un menú de 7 opciones: verificar cobertura, actualizar datos, consultar registros, estadísticas descriptivas, entrenar y evaluar la regresión, generar visualizaciones y salir. El detalle está en [cli-y-visualizaciones.md](cli-y-visualizaciones.md).
- **Consecuencias y limitaciones:** casi toda la lógica vive en Python; Java queda como una «capa de persistencia» invocada bajo demanda. Cada llamada a Java arranca una JVM, lo que añade una latencia de algunos segundos [Supuesto]. Es aceptable en una CLI académica.
- **Estado:** definitiva.

## D-002 — Java es el único que accede a ObjectDB

- **Contexto:** ObjectDB es una base de datos de objetos para Java que se usa mediante JPA [Verificado: [ObjectDB – conexión](https://www.objectdb.com/java/jpa/start/connection)]. Python no tiene un cliente oficial.
- **Opciones consideradas:** (a) solo Java abre el archivo `.odb`; (b) Python lee el archivo directamente; (c) se ejecuta un servidor ObjectDB y se accede a él por red desde Python.
- **Decisión:** (a). Python nunca abre ni interpreta los archivos internos de la base.
- **Consecuencias y limitaciones:** toda consulta necesita una exportación hecha por Java (ver D-003 y D-004). Las consultas ad hoc desde Python no son posibles sin pasar por Java. Leer el archivo directamente sería frágil y además la licencia prohíbe la ingeniería inversa [Verificado: [ObjectDB – licencia](https://www.objectdb.com/database/license)].
- **Estado:** definitiva.

## D-003 — Comunicación entre procesos mediante un JAR con subcomandos

- **Contexto:** Python necesita pedirle a Java tres cosas: la cobertura que hay guardada, que inserte un lote y que exporte datos.
- **Opciones consideradas:** (a) Python ejecuta un JAR con subcomandos (`coverage`, `import`, `export`) como proceso hijo; (b) un servidor HTTP local en Java; (c) Py4J u otro puente en memoria entre la JVM y Python; (d) intercambiar archivos CSV sin un protocolo definido.
- **Decisión:** (a). La comparación completa con las alternativas está en [arquitectura.md](arquitectura.md#justificación-frente-a-alternativas-descartadas).
- **Consecuencias y limitaciones:** el diseño es simple, fácil de probar a mano desde la terminal y sin estado entre llamadas. A cambio, arrancar la JVM en cada llamada tiene un coste, y la concurrencia sobre el archivo `.odb` debe evitarse: solo un proceso Java a la vez [Por verificar: comportamiento de bloqueo del archivo, Fase 4].
- **Estado:** definitiva. Los detalles (argumentos, códigos de salida) se fijan en la Fase 4.

## D-004 — Intercambio de lotes en JSON Lines y reglas de stdout/stderr

- **Contexto:** los lotes pueden tener miles de registros (un año horario son 8 760 horas) y las respuestas de control son pequeñas.
- **Opciones consideradas:** (a) lotes en archivos JSON Lines y respuestas pequeñas como JSON por stdout; (b) todo por stdout; (c) archivos CSV; (d) un único archivo JSON con una lista.
- **Decisión:** (a). Los archivos que Python entrega a Java van en `staging/` y los que Java exporta para Python van en `exchange/`. Por stdout solo viaja un objeto JSON; los mensajes de log van a stderr.
- **Consecuencias y limitaciones:** JSON Lines permite procesar línea a línea, detectar la línea exacta de un error y representar `null` de forma explícita, cosa que CSV no distingue bien de una cadena vacía. Como los archivos de `staging/` y `exchange/` son temporales, hay que definir cuándo se limpian (Fase 4).
- **Estado:** definitiva. El formato concreto de cada línea se fija en la Fase 4.

## D-005 — Meteorología: Open-Meteo Historical con ERA5 explícito

- **Contexto:** se necesitan la temperatura a 2 m, la humedad relativa a 2 m y el viento a 10 m de un año, con una sola fuente coherente.
- **Opciones consideradas:** ERA5, ERA5-Land, ERA5-Seamless, ECMWF IFS y *Best match*. La tabla está en [fuentes-y-datos.md](fuentes-y-datos.md#tabla-comparativa-de-fuentes).
- **Decisión:** ERA5 seleccionado de forma explícita.
  - *Best match* combina IFS HRES, ERA5 y ERA5-Land [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)], y eso podría cambiar el modelo de origen dentro de la serie.
  - ERA5-Land no ofrece velocidad del viento [Verificado: misma fuente].
  - ERA5-Seamless mezcla temperatura y humedad de ERA5-Land con viento de ERA5 [Verificado: misma fuente], es decir, dos resoluciones distintas en un mismo registro.
- **Consecuencias y limitaciones:** la resolución es de 0,25° (~25 km), la serie es horaria y hay un retraso de 5 días [Verificado: misma fuente]. Una celda de 25 km no resuelve el valle de Aburrá: es un promedio regional. El valor exacto del parámetro para pedir ERA5 está [Por verificar, Fase 1]; la página lo sugiere como `era5`.
- **Estado:** provisional, hasta comprobar en la Fase 1 que se reciben datos completos para Medellín.

## D-006 — Calidad del aire: PM2.5 de CAMS global vía Open-Meteo

- **Contexto:** se necesita una serie de PM2.5 de un año para Medellín.
- **Opciones consideradas:** (a) Open-Meteo Air Quality con el dominio global de CAMS; (b) el dominio europeo de CAMS, que no cubre Colombia; (c) estaciones de medición locales (por ejemplo, la red del valle de Aburrá), que quedan fuera del alcance por la decisión de usar una sola API.
- **Decisión:** (a), variable PM2.5, dominio `cams_global` [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api), valores `auto`, `cams_europe` y `cams_global`].
- **Consecuencias y limitaciones:**
  - **Es un modelo, no una medición.** El historial que ofrece la API son pronósticos archivados [Verificado: misma fuente: «access archived forecasts»].
  - La resolución es de 0,4° (~45 km) y el paso de 3 horas, con datos disponibles desde agosto de 2022 [Verificado: misma fuente].
  - Unidad: µg/m³; valor instantáneo a 10 m sobre el suelo [Verificado: misma fuente].
- **Motivo de revisión:** el paso nativo es de **3 horas**, pero el resto del diseño supone datos horarios (franjas con «2 de 3 horas», cobertura ≥ 98 % horaria, regresión horaria). Hay que comprobar en la Fase 1 si la API devuelve valores horarios interpolados o valores cada 3 horas con `null` en medio [Por verificar, Fase 1].
  - Si interpola, las horas intermedias no son información nueva: inflan artificialmente el tamaño de la muestra y la autocorrelación.
  - Si deja `null`, ninguna franja de PM2.5 alcanzaría 2 de 3 horas y la cobertura horaria sería de un 33 %.

  Las consecuencias de cada caso se tratan en [cobertura-y-franjas.md](cobertura-y-franjas.md#interacción-con-el-paso-de-3-horas-de-pm25) y [regresion.md](regresion.md#conjunto-de-datos).
- **Estado:** **pendiente de revisión** (Fase 1). La fuente no cambia; lo que debe revisarse es cómo se trata su resolución temporal.

## D-007 — Un único punto representativo de Medellín

- **Contexto:** las APIs devuelven series para una coordenada y la resolución de los modelos (25–45 km) es mayor que la ciudad.
- **Opciones consideradas:** (a) un punto en el centro; (b) varios puntos promediados; (c) varios puntos tratados como ubicaciones distintas.
- **Decisión:** (a). Las coordenadas exactas y la elevación que se fijará están [Por verificar, Fase 1]. La elevación importa porque Open-Meteo la usa para el reescalado estadístico (*downscaling*): por defecto toma un modelo digital de elevación de 90 m [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)].
- **Consecuencias y limitaciones:** con celdas de 25–45 km, varios puntos de Medellín caerían probablemente en la misma celda, así que más puntos no aportarían información real [Supuesto]. El modelo de datos (entidad Location) permite añadir ubicaciones más adelante.
- **Estado:** provisional.

## D-008 — Almacenar en UTC, calcular en America/Bogota

- **Contexto:** las franjas son locales (mañana, tarde, noche), pero las marcas de tiempo deben ser inequívocas.
- **Opciones consideradas:** (a) guardar en UTC y convertir al analizar; (b) guardar la hora local; (c) guardar ambas.
- **Decisión:** (a). Colombia usa UTC−5 sin horario de verano [Por verificar contra la base de datos tz, Fase 3]. La API devuelve por defecto horas en GMT [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)], lo que encaja con esta decisión.
- **Consecuencias y limitaciones:** cada análisis local requiere una conversión explícita, y la franja de la noche (19–21 h local) cae en el día UTC siguiente (00–02 UTC). Ver [cobertura-y-franjas.md](cobertura-y-franjas.md#zona-horaria-y-cambios-de-fecha).
- **Estado:** definitiva.

## D-009 — Franjas horarias mañana, tarde y noche

- **Contexto:** se quiere comparar momentos típicos del día. Las hipótesis iniciales son las 8:00, las 14:00 y las 20:00 locales.
- **Opciones consideradas:** (a) el valor de la hora puntual; (b) el promedio de una ventana de 3 horas con un mínimo de horas válidas; (c) el promedio sin mínimo; (d) interpolar los huecos.
- **Decisión:** (b), con las ventanas 7–9 h, 13–15 h y 19–21 h dentro del mismo día civil local. Cada franja necesita al menos 2 de sus 3 horas; si no las tiene, su valor es NaN. No se interpola.
- **Consecuencias y limitaciones:** el promedio es más robusto que una hora suelta, pero suaviza los picos.
- **Motivo de revisión:** ver D-006. Si PM2.5 llega cada 3 horas, sus pasos nativos en hora local serían las 7, 13 y 19 h [Supuesto: pasos en 00, 03, …, 21 UTC, por verificar en la Fase 1]. Cada ventana contendría así exactamente un dato real de PM2.5: o la regla de 2 de 3 horas no se cumple nunca, o se cumple con valores interpolados por la API, lo que contradice la regla de «no interpolar». Hay que decidir si la regla se aplica por variable según su paso nativo.
- **Estado:** **pendiente de revisión** (Fases 1 y 6).

## D-010 — Cuatro entidades en ObjectDB

- **Contexto:** hay que guardar los datos y su procedencia.
- **Opciones consideradas:** (a) Location, WeatherRecord, AirQualityRecord e IngestionBatch; (b) una sola entidad «Observación» con todas las variables; (c) una entidad por variable.
- **Decisión:** (a). Los campos y las relaciones están en [arquitectura.md](arquitectura.md#modelo-de-clases).
- **Consecuencias y limitaciones:** las fuentes tienen pasos y latencias distintos; separarlas evita filas con la mitad de los campos vacíos y deja la procedencia clara. La versión gratuita de ObjectDB admite hasta 10 clases de entidad y un millón de entidades por archivo [Verificado: [ObjectDB – compra](https://www.objectdb.com/database/purchase)]. Un año son unas 8 760 + 8 760 filas como máximo, muy por debajo del límite.
- **Estado:** provisional, hasta la prueba de la Fase 2.

## D-011 — Clave natural: ubicación + fuente + timestamp UTC

- **Contexto:** hay que impedir que un mismo dato se guarde dos veces si se descarga de nuevo.
- **Opciones consideradas:** (a) clave natural compuesta con una restricción de unicidad; (b) solo un identificador autogenerado, comprobando los duplicados en Python; (c) un hash de la fila.
- **Decisión:** (a). ObjectDB admite índices únicos compuestos (`@Unique` o `@Index` con varios miembros) y lanza una `PersistenceException` al confirmar una transacción con duplicados [Verificado: [ObjectDB – índices](https://www.objectdb.com/java/jpa/entity/index)]. Si un índice único puede incluir una referencia a Location, o si conviene usar el código de la ubicación, está [Por verificar, Fase 2].
- **Consecuencias y limitaciones:** la deduplicación ocurre en la base y no depende de que Python acierte. Un duplicado no debe abortar todo el lote; Java tiene que detectarlo y contarlo (ver D-013).
- **Estado:** definitiva en el concepto; la implementación se valida en la Fase 2.

## D-012 — Ausentes como null, nunca como 0

- **Contexto:** 0 °C, 0 % o 0 µg/m³ son valores físicamente posibles o al menos interpretables. Un 0 usado como «no hay dato» se confundiría con un dato real.
- **Opciones consideradas:** (a) `null`; (b) 0; (c) un valor centinela (−999).
- **Decisión:** (a) en toda la cadena: JSON Lines (`null`), entidades Java (tipos envoltorio que admiten null) y Pandas (NaN).
- **Consecuencias y limitaciones:** los promedios y las métricas deben ignorar los ausentes de forma explícita. Los campos numéricos en Java no pueden ser tipos primitivos [Supuesto: práctica estándar de JPA].
- **Estado:** definitiva.

## D-013 — Solo inserciones; correcciones mediante lote explícito

- **Contexto:** se quiere saber siempre de dónde viene cada valor y que una descarga nueva no borre una anterior por accidente.
- **Opciones consideradas:** (a) solo inserciones y saltar los duplicados; (b) *upsert* (insertar o sobrescribir); (c) borrar y recargar el periodo.
- **Decisión:** (a). Un registro existente solo puede cambiar mediante un IngestionBatch marcado como corrección.
- **Consecuencias y limitaciones:** si la fuente revisa datos recientes (posible en ERA5 [Por verificar, Fase 1]), la base conservará la primera versión salvo que se haga una corrección. Falta definir el mecanismo de corrección (¿se sobrescribe el valor y se apunta al nuevo lote?, ¿se guarda el valor anterior?) [decisión pendiente DP-04, Fase 2].
- **Estado:** provisional.

## D-014 — Criterio de cobertura: 98 % y hueco máximo de 6 h

- **Contexto:** antes de analizar hay que saber si los datos son suficientes.
- **Opciones consideradas:** solo un porcentaje; solo el hueco máximo; ambos.
- **Decisión:** el estado es COMPLETA si **cada variable** tiene una cobertura ≥ 98 % y un hueco máximo ≤ 6 h; PARCIAL si hay algún dato sin cumplir lo anterior; SIN_DATOS si no hay ninguno. Los umbrales son **decisiones de diseño, no estándares**. Ver [cobertura-y-franjas.md](cobertura-y-franjas.md#criterio-de-cobertura).
- **Consecuencias y limitaciones:** con 8 760 horas, el 98 % tolera unas 175 horas faltantes. El hueco máximo evita que esas horas se concentren en un solo tramo. Para PM2.5 el número de pasos esperados depende de D-006.
- **Estado:** provisional (Fase 5).

## D-015 — Actualización incremental respetando la latencia

- **Contexto:** el límite gratuito de Open-Meteo es de 10 000 llamadas al día, y las peticiones de más de 2 semanas o de más de 10 variables cuentan como varias llamadas [Verificado: [Open-Meteo – precios](https://open-meteo.com/en/pricing)].
- **Opciones consideradas:** (a) pedir solo los intervalos faltantes; (b) descargar el año entero cada vez.
- **Decisión:** (a). Además, no se piden fechas que la fuente todavía no publica: ERA5 llega con 5 días de retraso [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)]. En PM2.5 la API también devuelve pronósticos futuros, que nunca se guardan [Recomendación].
- **Consecuencias y limitaciones:** hace falta calcular los faltantes (Fase 5). Un intervalo cuya fuente no tiene datos se volverá a pedir en cada actualización; conviene registrarlo en IngestionBatch para no insistir indefinidamente [Recomendación].
- **Estado:** definitiva.

## D-016 — Ventana móvil de un año

- **Contexto:** el periodo de análisis se mueve con la fecha actual.
- **Decisión:** la ventana va de la fecha actual menos un año a la fecha actual, recortada por la latencia de cada fuente. El cálculo y el caso del 29 de febrero están en [cobertura-y-franjas.md](cobertura-y-franjas.md#ventana-móvil).
- **Consecuencias y limitaciones:** los resultados de dos ejecuciones en fechas distintas no son comparables directamente. Los datos que salen de la ventana no se borran (D-013); simplemente no se analizan.
- **Estado:** definitiva.

## D-017 — Regresión lineal: PM2.5 ~ temperatura + humedad + viento

- **Contexto:** el curso pide un análisis estadístico interpretable.
- **Opciones consideradas:** regresión lineal; árboles o *boosting*; redes neuronales.
- **Decisión:** regresión lineal múltiple con scikit-learn. Sin redes neuronales ni modelos complejos. Ver [regresion.md](regresion.md).
- **Consecuencias y limitaciones:** el modelo es fácil de explicar, pero no captura relaciones no lineales ni la dinámica temporal.
- **Estado:** definitiva.

## D-018 — Split temporal 9 + 3 meses con hueco de 24 h

- **Contexto:** los datos horarios están autocorrelacionados; un *split* aleatorio mezclaría horas vecinas entre entrenamiento y prueba.
- **Decisión:** los primeros ~9 meses se usan para entrenar y los últimos ~3 para probar, con 24 h descartadas entre ambos.
- **Consecuencias y limitaciones:** la prueba cubre una sola época del año, distinta de la del entrenamiento, así que las métricas dependen de la estacionalidad. Ver [regresion.md](regresion.md#separación-temporal-con-hueco).
- **Estado:** provisional (las proporciones exactas se fijan en la Fase 7).

## D-019 — Pipeline con escalador ajustado solo con entrenamiento

- **Decisión:** usar un Pipeline de scikit-learn (escalador + regresión) que se ajusta solo con el conjunto de entrenamiento.
- **Consecuencias y limitaciones:** evita la fuga de información; los coeficientes quedan en unidades estandarizadas. Ver [regresion.md](regresion.md#pipeline-y-prevención-de-fuga-de-información).
- **Estado:** definitiva.

## D-020 — Línea base y métricas

- **Decisión:** la línea base predice la media de PM2.5 en el entrenamiento. Las métricas son MAE, RMSE y R², calculadas sobre el conjunto de prueba para el modelo y la línea base.
- **Consecuencias y limitaciones:** un modelo que no supera la línea base no aporta capacidad predictiva. Ver [regresion.md](regresion.md#línea-base).
- **Estado:** definitiva.

## D-021 — Las franjas se calculan y no se persisten

- **Contexto:** las franjas son un resumen derivado y sus reglas pueden cambiar (ver D-009).
- **Opciones consideradas:** (a) calcularlas en Python en cada análisis; (b) guardarlas como entidad.
- **Decisión:** (a).
- **Consecuencias y limitaciones:** cambiar la regla no obliga a migrar la base, y no hay datos derivados que puedan quedar desactualizados. Además, una entidad más consumiría una de las 10 clases de la versión gratuita (D-010).
- **Estado:** definitiva.

## D-022 — Unidades canónicas

- **Contexto:** Open-Meteo devuelve por defecto la temperatura en °C, la humedad en % y el viento en km/h, y permite pedir el viento en m/s con `wind_speed_unit=ms` [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)]. PM2.5 llega en µg/m³ [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)].
- **Decisión:** guardar en °C, %, m/s y µg/m³, e incluir la unidad en el nombre del campo [Recomendación].
- **Consecuencias y limitaciones:** las unidades del SI facilitan comparar con la literatura; los coeficientes de la regresión se interpretan en esas unidades.
- **Estado:** provisional (Fase 3).

## D-023 — Visualizaciones con Matplotlib, en ventana o PNG

- **Decisión:** generar las gráficas con Matplotlib; mostrarlas en una ventana o guardarlas como PNG según elija el usuario. Ver [cli-y-visualizaciones.md](cli-y-visualizaciones.md).
- **Estado:** provisional (Fase 8).

## Limitaciones y supuestos

- Las decisiones D-001 a D-021 vienen del encargo inicial y no se volvieron a investigar. Solo se comprobaron contra la documentación oficial las afirmaciones marcadas como [Verificado].
- Dos decisiones (D-006 y D-009) quedan **pendientes de revisión** por la diferencia entre el paso de 3 horas de PM2.5 y el diseño horario. Ninguna se cambió; la duda se resuelve en la Fase 1.
- Los enlaces de verificación se consultaron el 2026-10-09. La documentación de Open-Meteo y de ObjectDB puede cambiar.
- La lista consolidada de decisiones pendientes (DP-xx) y su fase está en [fases.md](fases.md#decisiones-pendientes).
