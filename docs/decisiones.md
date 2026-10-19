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
| [D-003](#d-003--comunicación-entre-procesos-mediante-un-jar-con-subcomandos) | Comunicación por procesos: JAR con subcomandos | Definitiva | — |
| [D-004](#d-004--intercambio-de-lotes-en-json-lines-y-reglas-de-stdoutstderr) | Lotes en JSON Lines; stdout solo JSON; logs en stderr | Definitiva | — |
| [D-005](#d-005--meteorología-open-meteo-historical-con-era5-explícito) | Meteorología: ERA5 explícito (`models=era5`) | Definitiva | — |
| [D-006](#d-006--calidad-del-aire-pm25-de-cams-global-vía-open-meteo) | PM2.5 de CAMS global (modelo), tratado como horario | Definitiva | — |
| [D-007](#d-007--un-único-punto-representativo-de-medellín) | Un único punto representativo (`MED-CENTRO`, 1 495 m) | Definitiva | — |
| [D-008](#d-008--almacenar-en-utc-calcular-en-americabogota) | UTC para almacenar; America/Bogota para calcular | Definitiva | — |
| [D-009](#d-009--franjas-horarias-mañana-tarde-y-noche) | Franjas 7–9, 13–15 y 19–21 h, con un mínimo de 2 de 3 horas, para las 4 variables | Definitiva | — |
| [D-010](#d-010--cuatro-entidades-en-objectdb) | Cuatro entidades en ObjectDB | Definitiva | — |
| [D-011](#d-011--clave-natural-ubicación--fuente--timestamp-utc) | Clave natural: ubicación + fuente + timestamp UTC | Definitiva | — |
| [D-012](#d-012--ausentes-como-null-nunca-como-0) | Ausentes como null, nunca 0 | Definitiva | — |
| [D-013](#d-013--solo-inserciones-correcciones-mediante-lote-explícito) | Solo inserciones; sin correcciones | Definitiva | — |
| [D-014](#d-014--criterio-de-cobertura-98--y-hueco-máximo-de-6-h) | Cobertura COMPLETA: ≥ 98 % y hueco ≤ 6 h | Definitiva | — |
| [D-015](#d-015--actualización-incremental-respetando-la-latencia) | Actualización incremental respetando la latencia | Definitiva | — |
| [D-016](#d-016--ventana-móvil-de-un-año) | Ventana móvil de un año | Definitiva | — |
| [D-017](#d-017--regresión-lineal-pm25--temperatura--humedad--viento) | Regresión lineal: PM2.5 ~ temperatura + humedad + viento | Definitiva | — |
| [D-018](#d-018--split-temporal-9--3-meses-con-hueco-de-24-h) | Split temporal: 9 meses naturales + resto, con hueco de 24 h | Definitiva | — |
| [D-019](#d-019--pipeline-con-escalador-ajustado-solo-con-entrenamiento) | Pipeline con escalador ajustado solo con entrenamiento | Definitiva | — |
| [D-020](#d-020--línea-base-y-métricas) | Línea base = media del entrenamiento; MAE, RMSE y R² | Definitiva | — |
| [D-021](#d-021--las-franjas-se-calculan-y-no-se-persisten) | Las franjas se calculan y no se persisten | Definitiva | — |
| [D-022](#d-022--unidades-canónicas) | Unidades canónicas (°C, %, m/s, µg/m³) | Definitiva | — |
| [D-023](#d-023--visualizaciones-con-matplotlib-en-ventana-o-png) | Matplotlib, con salida en ventana o PNG | Definitiva | — |
| [D-024](#d-024--modelos-de-calendario-para-temperatura-humedad-y-pm25) | Modelos de calendario para temperatura, humedad y PM2.5 | Definitiva | — |

Las decisiones D-001 a D-021 vienen del encargo inicial (sección 2). D-022 y D-023 se añaden aquí porque se derivan de ellas y conviene dejarlas por escrito. Las decisiones que estaban abiertas se cerraron en la sesión de exploración del 2026-10-18, con los resultados de la Fase 1; el resultado completo está en [openspec/roadmap.md](../openspec/roadmap.md).

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
- **Consecuencias y limitaciones:** el diseño es simple, fácil de probar a mano desde la terminal y sin estado entre llamadas. A cambio, arrancar la JVM en cada llamada tiene un coste, y la concurrencia sobre el archivo `.odb` debe evitarse: solo un proceso Java a la vez: un segundo proceso que abre el mismo `.odb` falla de inmediato con un error de base de datos (código 3) [Verificado: PV-15, Fase 4].
- **Estado:** definitiva. Los argumentos y los códigos de salida se fijaron en la Fase 4 ([arquitectura.md](arquitectura.md#subcomandos)).

## D-004 — Intercambio de lotes en JSON Lines y reglas de stdout/stderr

- **Contexto:** los lotes pueden tener miles de registros (un año horario son 8 760 horas) y las respuestas de control son pequeñas.
- **Opciones consideradas:** (a) lotes en archivos JSON Lines y respuestas pequeñas como JSON por stdout; (b) todo por stdout; (c) archivos CSV; (d) un único archivo JSON con una lista.
- **Decisión:** (a). Los archivos que Python entrega a Java van en `staging/` y los que Java exporta para Python van en `exchange/`. Por stdout solo viaja un objeto JSON; los mensajes de log van a stderr.
- **Consecuencias y limitaciones:** JSON Lines permite procesar línea a línea, detectar la línea exacta de un error y representar `null` de forma explícita, cosa que CSV no distingue bien de una cadena vacía. Como los archivos de `staging/` y `exchange/` son temporales, se definió su limpieza en la Fase 4: el lote de `staging/` se borra tras una importación correcta y se conserva si falla; `exchange/` se sobrescribe en cada llamada.
- **Estado:** definitiva. El formato de cada línea se fijó en la Fase 4 ([arquitectura.md](arquitectura.md#formato-json-lines)).

## D-005 — Meteorología: Open-Meteo Historical con ERA5 explícito

- **Contexto:** se necesitan la temperatura a 2 m, la humedad relativa a 2 m y el viento a 10 m de un año, con una sola fuente coherente.
- **Opciones consideradas:** ERA5, ERA5-Land, ERA5-Seamless, ECMWF IFS y *Best match*. La tabla está en [fuentes-y-datos.md](fuentes-y-datos.md#tabla-comparativa-de-fuentes).
- **Decisión:** ERA5 seleccionado de forma explícita.
  - *Best match* combina IFS HRES, ERA5 y ERA5-Land [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)], y eso podría cambiar el modelo de origen dentro de la serie.
  - ERA5-Land no ofrece velocidad del viento [Verificado: misma fuente].
  - ERA5-Seamless mezcla temperatura y humedad de ERA5-Land con viento de ERA5 [Verificado: misma fuente], es decir, dos resoluciones distintas en un mismo registro.
- **Consecuencias y limitaciones:** la resolución es de 0,25° (~25 km), la serie es horaria y hay un retraso de 5 días [Verificado: misma fuente]. Una celda de 25 km no resuelve el valle de Aburrá: es un promedio regional. El parámetro es `models=era5` [Verificado: petición real, 2026-10-18]; la respuesta se ajusta a la celda (6,25, −75,5) y llega un año completo. Los últimos 2–3 meses son la versión preliminar ERA5T y se tratan como definitivos.
- **Estado:** definitiva (Fase 1).

## D-006 — Calidad del aire: PM2.5 de CAMS global vía Open-Meteo

- **Contexto:** se necesita una serie de PM2.5 de un año para Medellín.
- **Opciones consideradas:** (a) Open-Meteo Air Quality con el dominio global de CAMS; (b) el dominio europeo de CAMS, que no cubre Colombia; (c) estaciones de medición locales (por ejemplo, la red del valle de Aburrá), que quedan fuera del alcance por la decisión de usar una sola API.
- **Decisión:** (a), variable PM2.5, dominio `cams_global` [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api), valores `auto`, `cams_europe` y `cams_global`].
- **Consecuencias y limitaciones:**
  - **Es un modelo, no una medición.** El historial que ofrece la API son pronósticos archivados [Verificado: misma fuente: «access archived forecasts»].
  - La resolución es de 0,4° (~45 km) y el paso de 3 horas, con datos disponibles desde agosto de 2022 [Verificado: misma fuente].
  - Unidad: µg/m³; valor instantáneo a 10 m sobre el suelo [Verificado: misma fuente].
- **Resolución de la revisión (Fase 1):** la documentación indica un paso nativo de 3 horas, pero la API devuelve **24 valores horarios al día, sin nulos**, y las horas intermedias no son una interpolación simple [Verificado: `samples/cams_pm25_year.json`]. Por tanto:
  - La cobertura de PM2.5 se mide con pasos esperados horarios, igual que ERA5 (DP-03).
  - Las franjas usan la misma regla que las demás variables (DP-01).
  - La regresión usa todas las horas (DP-02).
  - El archivo empalma pronósticos a las 00 y 12 UTC, con saltos medios de 7,4 y 5,6 µg/m³ frente a 1,3 en el resto de horas. Los empalmes se documentan y se muestran en una gráfica, pero **no se corrigen** ([fuentes-y-datos.md](fuentes-y-datos.md#empalmes-de-las-ejecuciones-del-pronóstico-00-y-12-utc)).
- **Estado:** definitiva.

## D-007 — Un único punto representativo de Medellín

- **Contexto:** las APIs devuelven series para una coordenada y la resolución de los modelos (25–45 km) es mayor que la ciudad.
- **Opciones consideradas:** (a) un punto en el centro; (b) varios puntos promediados; (c) varios puntos tratados como ubicaciones distintas.
- **Decisión:** (a): ubicación `MED-CENTRO` («Medellín – Centro»), latitud 6,2447, longitud −75,5748, elevación fija de **1 495 m** (altitud oficial) y zona horaria America/Bogota. La elevación se envía como `elevation=1495` a la API de ERA5; la Air Quality API no documenta ese parámetro y no se envía. La elevación importa porque Open-Meteo la usa para el reescalado estadístico (*downscaling*): por defecto toma un modelo digital de elevación de 90 m [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)].
- **Consecuencias y limitaciones:** con celdas de 25–45 km, varios puntos de Medellín caerían probablemente en la misma celda, así que más puntos no aportarían información real [Supuesto]. El modelo de datos (entidad Location) permite añadir ubicaciones más adelante. El valor fijo se prefiere al automático (1 493 m) porque es explícito, reproducible y queda guardado en la base.
- **Estado:** definitiva (Fase 1).

## D-008 — Almacenar en UTC, calcular en America/Bogota

- **Contexto:** las franjas son locales (mañana, tarde, noche), pero las marcas de tiempo deben ser inequívocas.
- **Opciones consideradas:** (a) guardar en UTC y convertir al analizar; (b) guardar la hora local; (c) guardar ambas.
- **Decisión:** (a). Colombia usa UTC−5 sin horario de verano [Verificado: la base de datos tz da UTC−5 en todas las horas de 2025 y 2026, prueba `test_bogota_is_utc_minus_5_all_year`, Fase 3]. La API devuelve por defecto horas en GMT [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)], lo que encaja con esta decisión.
- **Consecuencias y limitaciones:** cada análisis local requiere una conversión explícita, y la franja de la noche (19–21 h local) cae en el día UTC siguiente (00–02 UTC). Ver [cobertura-y-franjas.md](cobertura-y-franjas.md#zona-horaria-y-cambios-de-fecha).
- **Estado:** definitiva.

## D-009 — Franjas horarias mañana, tarde y noche

- **Contexto:** se quiere comparar momentos típicos del día. Las hipótesis iniciales son las 8:00, las 14:00 y las 20:00 locales.
- **Opciones consideradas:** (a) el valor de la hora puntual; (b) el promedio de una ventana de 3 horas con un mínimo de horas válidas; (c) el promedio sin mínimo; (d) interpolar los huecos.
- **Decisión:** (b), con las ventanas 7–9 h, 13–15 h y 19–21 h dentro del mismo día civil local. Cada franja necesita al menos 2 de sus 3 horas; si no las tiene, su valor es NaN. No se interpola.
- **Consecuencias y limitaciones:** el promedio es más robusto que una hora suelta, pero suaviza los picos.
- **Resolución de la revisión (Fase 1):** PM2.5 llega con 24 valores horarios (ver D-006), así que la regla de 2 de 3 horas se aplica **igual a las 4 variables** (DP-01). Advertencia: las franjas de la mañana (07–09) y de la noche (19–21) empiezan en un empalme del pronóstico de CAMS (12 y 00 UTC); se documenta en [cobertura-y-franjas.md](cobertura-y-franjas.md#pm25-horario-y-empalmes-del-pronóstico).
- **Estado:** definitiva.

## D-010 — Cuatro entidades en ObjectDB

- **Contexto:** hay que guardar los datos y su procedencia.
- **Opciones consideradas:** (a) Location, WeatherRecord, AirQualityRecord e IngestionBatch; (b) una sola entidad «Observación» con todas las variables; (c) una entidad por variable.
- **Decisión:** (a). Los campos y las relaciones están en [arquitectura.md](arquitectura.md#modelo-de-clases).
- **Consecuencias y limitaciones:** las fuentes tienen pasos y latencias distintos; separarlas evita filas con la mitad de los campos vacíos y deja la procedencia clara. La versión gratuita de ObjectDB admite hasta 10 clases de entidad y un millón de entidades por archivo [Verificado: [ObjectDB – compra](https://www.objectdb.com/database/purchase)]. Un año son unas 8 760 + 8 760 filas como máximo, muy por debajo del límite.
- **Estado:** definitiva (Fase 2: las cuatro entidades funcionan con las pruebas de `RecordStoreTest`).

## D-011 — Clave natural: ubicación + fuente + timestamp UTC

- **Contexto:** hay que impedir que un mismo dato se guarde dos veces si se descarga de nuevo.
- **Opciones consideradas:** (a) clave natural compuesta con una restricción de unicidad; (b) solo un identificador autogenerado, comprobando los duplicados en Python; (c) un hash de la fila.
- **Decisión:** (a). ObjectDB admite índices únicos compuestos (`@Unique` o `@Index` con varios miembros) y lanza una `PersistenceException` al confirmar una transacción con duplicados [Verificado: [ObjectDB – índices](https://www.objectdb.com/java/jpa/entity/index)]. El índice único admite la referencia a Location (`@Unique(members = {"location", "source", "timestampUtc"})`) [Verificado: Fase 2].
- **Consecuencias y limitaciones:** la deduplicación ocurre en la base y no depende de que Python acierte. Un duplicado no debe abortar todo el lote; Java tiene que detectarlo y contarlo (ver D-013).
- **Estado:** definitiva (implementación validada en la Fase 2: precarga de claves existentes, conteo de duplicados y bloques de 500).

## D-012 — Ausentes como null, nunca como 0

- **Contexto:** 0 °C, 0 % o 0 µg/m³ son valores físicamente posibles o al menos interpretables. Un 0 usado como «no hay dato» se confundiría con un dato real.
- **Opciones consideradas:** (a) `null`; (b) 0; (c) un valor centinela (−999).
- **Decisión:** (a) en toda la cadena: JSON Lines (`null`), entidades Java (tipos envoltorio que admiten null) y Pandas (NaN).
- **Consecuencias y limitaciones:** los promedios y las métricas deben ignorar los ausentes de forma explícita. Los campos numéricos en Java no pueden ser tipos primitivos [Supuesto: práctica estándar de JPA].
- **Estado:** definitiva.

## D-013 — Solo inserciones; correcciones mediante lote explícito

- **Contexto:** se quiere saber siempre de dónde viene cada valor y que una descarga nueva no borre una anterior por accidente.
- **Opciones consideradas:** (a) solo inserciones y saltar los duplicados; (b) *upsert* (insertar o sobrescribir); (c) borrar y recargar el periodo.
- **Decisión:** (a), **sin mecanismo de corrección** (DP-04): un registro existente nunca cambia y `IngestionBatch.type` vale siempre `NORMAL`. Los lotes de tipo `CORRECCION` quedan como posible extensión futura, fuera del alcance.
- **Consecuencias y limitaciones:** si la fuente revisa datos recientes (posible en ERA5T), la base conserva la primera versión, coherente con tratar ERA5T como definitivo. Un solo camino de escritura: transacciones, clave natural, idempotencia y procedencia, sin rutas de actualización.
- **Estado:** definitiva.

## D-014 — Criterio de cobertura: 98 % y hueco máximo de 6 h

- **Contexto:** antes de analizar hay que saber si los datos son suficientes.
- **Opciones consideradas:** solo un porcentaje; solo el hueco máximo; ambos.
- **Decisión:** el estado es COMPLETA si **cada variable** tiene una cobertura ≥ 98 % y un hueco máximo ≤ 6 h; PARCIAL si hay algún dato sin cumplir lo anterior; SIN_DATOS si no hay ninguno. Los umbrales son **decisiones de diseño, no estándares**. Ver [cobertura-y-franjas.md](cobertura-y-franjas.md#criterio-de-cobertura).
- **Consecuencias y limitaciones:** con 8 760 horas, el 98 % tolera unas 175 horas faltantes. El hueco máximo evita que esas horas se concentren en un solo tramo. Para PM2.5 el número de pasos esperados depende de D-006.
- **Estado:** definitiva (Fase 5). Los pasos esperados son horarios para las dos fuentes (DP-03) y los umbrales se aplican por variable en `coverage.state_of`.

## D-015 — Actualización incremental respetando la latencia

- **Contexto:** el límite gratuito de Open-Meteo es de 10 000 llamadas al día, y las peticiones de más de 2 semanas o de más de 10 variables cuentan como varias llamadas [Verificado: [Open-Meteo – precios](https://open-meteo.com/en/pricing)].
- **Opciones consideradas:** (a) pedir solo los intervalos faltantes; (b) descargar el año entero cada vez.
- **Decisión:** (a). Además, no se piden fechas que la fuente todavía no publica: ERA5 llega con 5 días de retraso [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)]. En PM2.5 la API también devuelve pronósticos futuros, que nunca se guardan [Recomendación].
- **Consecuencias y limitaciones:** los faltantes se calculan en Python a partir de los timestamps que devuelve `coverage` (Fase 5). Un intervalo cuya fuente no tiene datos se vuelve a pedir en cada actualización, y cada intento queda registrado como un IngestionBatch con 0 insertados. Las filas con todas las variables a `null` no se guardan nunca (DP-12): así siguen contando como faltantes y se vuelven a pedir en la siguiente actualización. Las horas de ERA5 aún no publicadas, que la API devuelve como `null`, se descartan por la misma regla y por el recorte en el fin efectivo.
- **Estado:** definitiva.

## D-016 — Ventana móvil de un año

- **Contexto:** el periodo de análisis se mueve con la fecha actual.
- **Decisión:** la ventana va de la fecha actual menos un año a la fecha actual, recortada por la latencia de cada fuente: el fin efectivo de ERA5 es las 00:00 UTC de D−4 (el día D−5 es el último completo) y el de CAMS es el fin de la ventana. El 29 de febrero se sustituye por el 28 de febrero del año anterior (DP-09). El cálculo y el caso del 29 de febrero están en [cobertura-y-franjas.md](cobertura-y-franjas.md#ventana-móvil).
- **Consecuencias y limitaciones:** los resultados de dos ejecuciones en fechas distintas no son comparables directamente. Los datos que salen de la ventana no se borran (D-013); simplemente no se analizan.
- **Estado:** definitiva.

## D-017 — Regresión lineal: PM2.5 ~ temperatura + humedad + viento

- **Contexto:** el curso pide un análisis estadístico interpretable.
- **Opciones consideradas:** regresión lineal; árboles o *boosting*; redes neuronales.
- **Decisión:** regresión lineal múltiple con scikit-learn. Sin redes neuronales ni modelos complejos. Ver [regresion.md](regresion.md).
- **Consecuencias y limitaciones:** el modelo es fácil de explicar, pero no captura relaciones no lineales ni la dinámica temporal. Se usan todas las horas de PM2.5 (DP-02) en escala original (DP-08). Implementado en `regression.py` (Fase 7); con las muestras apenas mejora la línea base ([regresion.md](regresion.md#resultado-con-las-muestras)).
- **Estado:** definitiva.

## D-018 — Split temporal 9 + 3 meses con hueco de 24 h

- **Contexto:** los datos horarios están autocorrelacionados; un *split* aleatorio mezclaría horas vecinas entre entrenamiento y prueba.
- **Decisión:** entrenamiento = [inicio de la ventana, inicio + 9 meses naturales); después se descartan 24 h; prueba = el resto de la ventana. Si el día no existe nueve meses después, se usa el último día de ese mes. Las fechas exactas se imprimen con los resultados. El perfil diurno se calcula solo con el entrenamiento. Ejemplo: con la ventana 2025-10-18 → 2026-10-18 (hora local), entrenamiento hasta el 2026-07-18 y prueba desde el 2026-07-19, a las 00:00 locales (implementado en `split.temporal_split`, Fase 6).
- **Consecuencias y limitaciones:** la prueba cubre una sola época del año, distinta de la del entrenamiento, así que las métricas dependen de la estacionalidad. Ver [regresion.md](regresion.md#separación-temporal-con-hueco).
- **Estado:** definitiva.

## D-019 — Pipeline con escalador ajustado solo con entrenamiento

- **Decisión:** usar un Pipeline de scikit-learn (escalador + regresión) que se ajusta solo con el conjunto de entrenamiento.
- **Consecuencias y limitaciones:** evita la fuga de información; los coeficientes quedan en unidades estandarizadas y se convierten también a unidades originales dividiendo entre la desviación de entrenamiento. Una prueba comprueba que el escalador aprende la media del entrenamiento y no la de todo el periodo. Ver [regresion.md](regresion.md#pipeline-y-prevención-de-fuga-de-información).
- **Estado:** definitiva.

## D-020 — Línea base y métricas

- **Decisión:** la línea base predice la media de PM2.5 en el entrenamiento. Las métricas son MAE, RMSE y R², calculadas sobre el conjunto de prueba para el modelo y la línea base.
- **Consecuencias y limitaciones:** un modelo que no supera la línea base no aporta capacidad predictiva. Se completan con VIF (entrenamiento) y Durbin-Watson (residuos de prueba), sin p-valores por la autocorrelación. Ver [regresion.md](regresion.md#línea-base).
- **Estado:** definitiva.

## D-021 — Las franjas se calculan y no se persisten

- **Contexto:** las franjas son un resumen derivado y sus reglas pueden cambiar (ver D-009).
- **Opciones consideradas:** (a) calcularlas en Python en cada análisis; (b) guardarlas como entidad.
- **Decisión:** (a).
- **Consecuencias y limitaciones:** cambiar la regla no obliga a migrar la base, y no hay datos derivados que puedan quedar desactualizados. Además, una entidad más consumiría una de las 10 clases de la versión gratuita (D-010).
- **Estado:** definitiva.

## D-022 — Unidades canónicas

- **Contexto:** Open-Meteo devuelve por defecto la temperatura en °C, la humedad en % y el viento en km/h, y permite pedir el viento en m/s con `wind_speed_unit=ms` [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)]. PM2.5 llega en µg/m³ [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)].
- **Decisión:** guardar en °C, %, m/s y µg/m³, e incluir la unidad en el nombre del campo. El viento se pide directamente en m/s con `wind_speed_unit=ms` (DP-06), así que no hay conversión.
- **Consecuencias y limitaciones:** las unidades del SI facilitan comparar con la literatura; los coeficientes de la regresión se interpretan en esas unidades.
- **Estado:** definitiva.

## D-023 — Visualizaciones con Matplotlib, en ventana o PNG

- **Decisión:** generar las gráficas con Matplotlib. La aplicación pregunta cada vez si mostrarlas en una ventana o guardarlas como PNG (`outputs/<gráfica>_<AAAAmmdd-HHMMSS>.png`); si no hay pantalla disponible, guarda el PNG automáticamente y lo avisa (DP-10). Cada gráfica lleva título, unidades, periodo y «Datos: Open-Meteo.com (ERA5, CAMS)». Implementado en la Fase 8 (`plots.py`), con 9 gráficas: las 8 previstas y el diagnóstico de empalmes. Ver [cli-y-visualizaciones.md](cli-y-visualizaciones.md).
- **Estado:** definitiva.

## D-024 — Modelos de calendario para temperatura, humedad y PM2.5

- **Contexto:** se quiere predecir la temperatura, la humedad y el PM2.5 para una hora, un día o un rango de fechas. La regresión de D-017 no sirve: necesita la meteorología de esa hora (exploración del 2026-10-19).
- **Opciones consideradas:** (a) regresión lineal con rasgos de calendario; (b) el perfil diurno como tabla de consulta; (c) pronósticos de Open-Meteo como entrada de la regresión de PM2.5; (d) más años de datos (5 años).
- **Decisión:** (a). Un modelo por variable, con 23 indicadores de hora local y la onda estacional seno/coseno, sin escalador. Se evalúa con la separación de D-018 frente a la media de entrenamiento y se reajusta con toda la ventana para predecir; su MAE de prueba es el «error típico». Los modelos se reentrenan en cada uso y no se guardan.
- **Consecuencias y limitaciones:** (a) superó a (b) en las tres variables; (c) contradice el alcance (sin pronósticos externos); (d) empeoró los resultados en una prueba sobre 11 trimestres (cambios de régimen entre años), así que la ventana sigue siendo de un año (D-016). Predice valores típicos, no el tiempo de un día concreto. Ver [regresion.md](regresion.md#modelos-de-calendario).
- **Estado:** definitiva.

## Limitaciones y supuestos

- Las decisiones D-001 a D-021 vienen del encargo inicial y no se volvieron a investigar. Solo se comprobaron contra la documentación oficial las afirmaciones marcadas como [Verificado].
- D-006 y D-009 estuvieron pendientes de revisión por el paso de 3 horas de PM2.5; la Fase 1 mostró que la API entrega valores horarios y ambas quedaron definitivas sin cambiar la fuente ni las franjas.
- Los enlaces de verificación se consultaron el 2026-10-09. La documentación de Open-Meteo y de ObjectDB puede cambiar.
- La lista de decisiones DP-xx, todas resueltas el 2026-10-18, está en [fases.md](fases.md#decisiones-pendientes). D-010 y D-011 se confirmaron en la Fase 2 y D-014 en la Fase 5.
