# Arquitectura

Este documento explica cómo está organizada la aplicación: qué hace Python, qué hace Java, cómo se comunican y cómo se modelan los datos en ObjectDB. El objetivo es que el estudiante pueda dibujar el flujo en una pizarra y justificar cada pieza frente a sus alternativas. Las decisiones que se apoyan en este documento son D-001 a D-004, D-010 a D-013 y D-021 ([decisiones.md](decisiones.md)).

## Idea general

La aplicación tiene **dos procesos con responsabilidades separadas**:

- **Python** es el «cerebro»: muestra el menú, descarga datos de Open-Meteo, los limpia con Pandas, calcula la cobertura, las franjas y las estadísticas, entrena la regresión y dibuja las gráficas.
- **Java** es el «guardián» de la base: es el único programa que abre el archivo de ObjectDB. Recibe lotes de Python y los inserta, responde preguntas sobre lo que hay guardado y exporta datos cuando Python los necesita.

Una analogía: Python es el investigador y Java el archivero de una biblioteca de acceso restringido. El investigador nunca entra al depósito; entrega formularios (archivos en `staging/`) y recibe copias (archivos en `exchange/`).

## Diagrama del flujo completo

```text
                         ┌────────────────────────────────────────┐
                         │  Open-Meteo                            │
                         │  · Historical Weather API (ERA5)       │
                         │  · Air Quality API (CAMS global)       │
                         └──────────────────┬─────────────────────┘
                                            │ HTTPS, respuesta JSON
                                            ▼
┌───────────────────────────────── PYTHON (orquestador) ──────────────────────────────────┐
│                                                                                          │
│  CLI (menú de 7 opciones)                                                                │
│    │                                                                                     │
│    ├─► Cobertura ──────────── pide a Java «coverage» ◄── JSON por stdout                 │
│    │       └─ calcula los intervalos faltantes (ventana móvil, latencia)                 │
│    │                                                                                     │
│    ├─► Ingesta ── descarga solo los faltantes ─► normaliza (Pandas: UTC, unidades,       │
│    │              rangos, duplicados, null) ─► escribe un lote .jsonl en staging/        │
│    │              └─ invoca a Java «import» ◄── resumen JSON por stdout                  │
│    │                                                                                     │
│    └─► Análisis ── invoca a Java «export» ─► lee el .jsonl de exchange/                  │
│                   ─► DataFrame ─► franjas · estadística · regresión · gráficas           │
│                                                                                          │
└──────────────┬────────────────────────────▲──────────────────────────────────────────────┘
               │ proceso hijo:              │ stdout: un único objeto JSON
               │ java -jar … <subcomando>   │ stderr: logs
               │ archivos: staging/ ──►     │ ◄── archivos: exchange/
               ▼                            │ código de salida
┌──────────────────────────────── JAVA (persistencia) ────────────────────────────────────┐
│                                                                                          │
│  coverage │ import │ export          JPA (EntityManager, transacciones)                  │
│                                                │                                         │
│                                                ▼                                         │
│                                   ObjectDB: archivo .odb                                 │
│                    Location · WeatherRecord · AirQualityRecord · IngestionBatch          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Flujo paso a paso

Ejemplo: el usuario elige «Actualizar datos» con la base vacía.

1. **Cobertura actual.** Python ejecuta el JAR con `coverage`. Java abre la base, cuenta los registros por ubicación, fuente y variable, calcula el primer y el último timestamp y devuelve un JSON por stdout. Con la base vacía, el estado es SIN_DATOS.
2. **Cálculo de faltantes.** Python calcula la ventana móvil (fecha actual − 1 año → fecha actual), la recorta según la latencia de cada fuente (ERA5: 5 días) y obtiene los intervalos sin datos. Ver [cobertura-y-franjas.md](cobertura-y-franjas.md#cálculo-de-faltantes-e-intervalos).
3. **Descarga.** Para cada intervalo y fuente, Python llama a la API correspondiente con las coordenadas de la ubicación, las variables, el modelo fijado y el rango de fechas.
4. **Normalización.** Python convierte la respuesta en un DataFrame:
   - Timestamps en UTC.
   - Unidades canónicas (D-022).
   - Rangos plausibles validados; los valores imposibles pasan a `null` y quedan registrados.
   - Duplicados eliminados dentro del lote.
   - En PM2.5, se descartan las horas del pronóstico futuro.
5. **Entrega a Java.** Python escribe un archivo JSON Lines en `staging/` (una línea por timestamp) y ejecuta el JAR con `import`, indicando la ruta del archivo y los metadatos del lote.
6. **Inserción.** Java crea un IngestionBatch, lee el archivo línea a línea y, dentro de transacciones, inserta los registros nuevos y omite los que ya existen por su clave natural (D-011, D-013). Al terminar escribe por stdout un resumen JSON (recibidos, insertados, duplicados omitidos, rechazados) y termina con código 0.
7. **Confirmación.** Python muestra el resumen y vuelve a pedir la cobertura para comprobar el nuevo estado.
8. **Análisis** (otras opciones del menú). Python ejecuta el JAR con `export`. Java escribe en `exchange/` los registros de la ventana pedida y devuelve por stdout la ruta y el número de líneas. Python carga el archivo en un DataFrame y calcula franjas, estadísticas, la regresión o las gráficas, sin volver a tocar la base.

## Protocolo de comunicación

### Subcomandos

Todos aceptan `--db <ruta>` (por defecto `data/clima.odb`); Python siempre lo pasa explícito. Las opciones son pares `--nombre valor` (definitivos, Fase 4).

| Subcomando | Opciones | Efecto | Respuesta por stdout |
|---|---|---|---|
| `import` | `--file <jsonl>` y `--meta <json>` con la fuente, la ubicación (`code`, `name`, `latitude`, `longitude`, `elevation_m`, `timezone`), `requested_start_utc`, `requested_end_utc`, `endpoint`, `params` y `notes` | Valida **todas** las líneas antes de escribir; asegura la ubicación; inserta en bloques de 500 y crea el IngestionBatch (tipo `NORMAL`) | `{"ok":true,"batch_id","received","inserted","duplicates","rejected"}` |
| `coverage` | `--location`, `--source`, `--out <jsonl>` | Solo lectura; escribe en `--out` una línea `{"timestamp_utc","non_null":[...]}` por timestamp guardado | `{"ok":true,"location","source","count","non_null":{variable: n},"first","last","file","lines"}` |
| `export` | `--location`, `--source`, `--from <ISO>`, `--to <ISO>`, `--out <jsonl>` | Solo lectura; escribe los registros de [from, to) ordenados, con `batch_id` | `{"ok":true,"file","lines"}` |

Ejemplo real:

```text
$ java -jar java/target/clima-medellin.jar coverage --db data/clima.odb --location MED-CENTRO --source ERA5 --out exchange/coverage-ERA5.jsonl
{"ok":true,"location":"MED-CENTRO","source":"ERA5","count":0,"non_null":{"temperature_2m_c":0,"relative_humidity_2m_pct":0,"wind_speed_10m_ms":0},"first":null,"last":null,"file":"exchange/coverage-ERA5.jsonl","lines":0}
```

**Formato de `coverage` (PV-19, resuelto en la Fase 4):** stdout lleva solo el resumen y la lista de timestamps va a un archivo de `exchange/`, con las variables no nulas de cada uno. Todos los cálculos de cobertura (porcentajes, huecos, intervalos faltantes) los hace Python, donde son funciones puras fáciles de probar.

### Reglas de stdout y stderr

- **stdout contiene exactamente un objeto JSON** al final de la ejecución, y nada más. Python lo interpreta como respuesta. Cualquier otro texto en stdout rompería el análisis de la respuesta.
- **stderr recibe todos los logs** (progreso, avisos, trazas de excepciones). Python puede mostrarlos u ocultarlos según un nivel de detalle.
- Si algo falla, Java escribe igualmente, si puede, un JSON de error por stdout (con un tipo y un mensaje) y termina con un código distinto de 0.

### Códigos de salida

| Código | Significado |
|---|---|
| 0 | Éxito (puede incluir duplicados omitidos, que no son error) |
| 1 | Error de uso: subcomando o argumentos inválidos |
| 2 | Error de datos: archivo inexistente, línea JSON inválida o violación de esquema |
| 3 | Error de base de datos: no se puede abrir el archivo, está bloqueado o falla una transacción |
| 4 | Error inesperado |

Separar los códigos permite a Python dar mensajes útiles («la base está en uso por otro proceso» frente a «el lote tiene una línea corrupta»). La tabla es definitiva (DP-05); Python la traduce a mensajes en español ([implementacion.md](implementacion.md#42-el-contrato-un-json-por-stdout-y-un-código-de-salida)).

### Formato JSON Lines

- Codificación UTF-8, una línea por registro y sin comas entre líneas.
- Timestamps en ISO 8601 con zona `Z` (UTC).
- Ausentes como `null` (D-012); nunca 0 ni cadena vacía.
- Unidades en el nombre del campo (D-022).
- Un archivo contiene registros de una sola fuente.

**Ejemplo ficticio** (los valores son inventados y no proceden de ninguna API; ilustran solo el formato de una línea de `staging/` para meteorología):

```text
{"location_code": "MED-CENTRO", "source": "ERA5", "timestamp_utc": "2026-03-01T13:00:00Z", "temperature_2m_c": 21.4, "relative_humidity_2m_pct": 78.0, "wind_speed_10m_ms": null}
```

En el ejemplo, `wind_speed_10m_ms` es `null`: ese valor no llegó en la respuesta y no debe confundirse con calma (0 m/s).

### Ciclo de vida de los archivos

- `staging/`: Python crea un archivo nuevo por lote (`<fuente>-<AAAAmmddTHHMMSSffffff>.jsonl`), Java lo lee y, si el import termina con código 0, Python lo **borra**. Si falla, se **conserva** y su ruta aparece en el mensaje de error.
- `exchange/`: Java escribe `export-<fuente>.jsonl` y `coverage-<fuente>.jsonl` (nombre fijo) y Python los lee. Se sobrescriben en cada llamada; salir de la aplicación no borra nada.
- Ambas carpetas son temporales y no se versionan en git [Recomendación].

## Modelo de clases

### Entidades

| Entidad | Propósito | Campos principales (definitivos, Fase 2) | Clave natural | Relaciones |
|---|---|---|---|---|
| **Location** | Punto geográfico del que se piden datos | id técnico, `code` (p. ej. «MED-CENTRO»), nombre, latitud, longitud, elevación (m), zona horaria («America/Bogota») | `code` | Referenciada por los registros y los lotes |
| **WeatherRecord** | Un paso horario de meteorología | id técnico, ubicación, fuente («ERA5»), `timestampUtc`, `temperature2mC`, `relativeHumidity2mPct`, `windSpeed10mMs` (los tres admiten null), lote | ubicación + fuente + `timestampUtc` | Muchos a uno con Location; muchos a uno con IngestionBatch |
| **AirQualityRecord** | Un paso de calidad del aire | id técnico, ubicación, fuente («CAMS_GLOBAL»), `timestampUtc`, `pm25UgM3` (admite null), lote | ubicación + fuente + `timestampUtc` | Muchos a uno con Location; muchos a uno con IngestionBatch |
| **IngestionBatch** | Procedencia: una descarga concreta | id técnico, identificador del lote (`batchId`, UUID en texto), fuente, ubicación, tipo (siempre `NORMAL`, DP-04), inicio y fin pedidos (UTC), momento de la ingesta (UTC), endpoint y parámetros usados, conteos (recibidos, insertados, duplicados, rechazados), notas | identificador del lote | Uno a muchos con los registros (navegable desde el registro) |

```text
              ┌──────────────┐
              │   Location   │
              └──────┬───────┘
          1          │ 1            1
   ┌─────────────────┼──────────────────┐
   │ *               │ *                │ *
┌──▼────────────┐ ┌──▼──────────────┐ ┌─▼───────────────┐
│ WeatherRecord │ │ AirQualityRecord│ │ IngestionBatch  │
└──────┬────────┘ └──────┬──────────┘ └─▲───────────────┘
       │ *               │ *            │ 1
       └─────────────────┴──────────────┘
         cada registro apunta al lote que lo insertó
```

### Notas de diseño

- **Clave natural y unicidad.** ObjectDB admite índices únicos compuestos y lanza una `PersistenceException` al confirmar una transacción con duplicados [Verificado: [ObjectDB – índices](https://www.objectdb.com/java/jpa/entity/index)]. El índice `@Unique(members = {"location", "source", "timestampUtc"})` (anotación `javax.jdo.annotations.Unique`, incluida en ObjectDB) **admite el campo de relación** con Location, así que no se repite el código de la ubicación [Verificado: prueba `databaseRejectsADuplicateNaturalKeyEvenWithoutTheService`, Fase 2].
- **Duplicados sin abortar el lote.** Como la excepción llega al confirmar, un solo duplicado podría deshacer toda la transacción. Implementación (Fase 2): se cargan antes los timestamps existentes del rango del lote, se descartan los duplicados (de la base y del propio lote), se rechazan las filas sin timestamp o con todo a `null`, y se confirma en bloques de 500; si un bloque falla, sus registros se reintentan uno a uno. Ver [implementacion.md](implementacion.md#25-insertar-un-lote-duplicados-y-bloques-de-500).
- **Tipo del timestamp.** Se usa `java.time.Instant`, que representa un instante UTC sin ambigüedad. ObjectDB lo guarda y lo devuelve exacto aunque la JVM que lee tenga otra zona horaria [Verificado: prueba `timestampRoundTripsExactlyInAnotherJvmTimeZone`, Fase 2].
- **Claves primarias compuestas.** ObjectDB las admite [Verificado: [ObjectDB – claves primarias](https://www.objectdb.com/java/jpa/entity/id)], pero se recomienda un id técnico más un índice único sobre la clave natural, porque es más sencillo de manejar [Recomendación].
- **Límites de la versión gratuita.** Hay 4 clases de entidad, frente a un máximo de 10, y unas 17 500 entidades por año, frente a un máximo de un millón por archivo [Verificado: [ObjectDB – compra](https://www.objectdb.com/database/purchase)]. Las clases que ObjectDB no encuentra al cargar un archivo antiguo podrían contar contra el límite [Supuesto: según un hilo del foro oficial; no se usará como fuente].
- **Versión y Java.** ObjectDB 2.9.5 (publicada el 2026-03-02) requiere Java 8 o superior con la variante `javax` y Java 17 o superior con la variante `jakarta` [Verificado: [ObjectDB – descarga](https://www.objectdb.com/download)]. Se usa la variante `jakarta` (`objectdb-jk`) con Java 25 (DP-07); ObjectDB declara la API de JPA como `provided`, así que el proyecto añade `jakarta.persistence-api` 3.1.0 para incluirla en el JAR.
- **Apertura de la base.** Basta con una URL `objectdb:` y la ruta del archivo; si el archivo no existe, se crea. No hace falta `persistence.xml` [Verificado: [ObjectDB – conexión](https://www.objectdb.com/java/jpa/start/connection)]. Al abrir, las cuatro entidades se registran con `em.getMetamodel().entity(...)`: sin ello, consultar una entidad que aún no tiene objetos falla con «Type ... is not found» [Verificado: Fase 2].
- **Archivos auxiliares de ObjectDB.** ObjectDB escribe sus registros internos en un directorio `log/` junto al JAR que lo contiene (`java/target/log/`, ignorado por git) y, con Java 25, imprime en stderr un aviso sobre `sun.misc.Unsafe`; stdout no se ve afectado [Verificado: Fase 2].

## Justificación frente a alternativas descartadas

| Alternativa | Qué sería | Por qué se descarta |
|---|---|---|
| **CSV** para el intercambio | Tablas de texto separadas por comas | No distingue bien `null` de una cadena vacía, depende del separador decimal y de la configuración regional, y no tiene tipos. JSON Lines conserva `null`, números y cadenas, y sigue permitiendo procesar línea a línea. |
| **Servidor HTTP local** en Java | Java como servicio REST en localhost | Exige gestionar el ciclo de vida de un servidor (arranque, puerto, parada) y añade complejidad de red sin beneficio en una CLI de un solo usuario. Las llamadas por proceso son más fáciles de probar a mano. |
| **Py4J** u otro puente en memoria | Python llama a objetos Java dentro de una JVM compartida | Acopla los dos lenguajes, complica la depuración y añade una dependencia; los errores de un lado se manifiestan de formas poco claras en el otro. El protocolo por procesos y archivos se puede inspeccionar con un editor de texto. |
| **Entidades combinadas** (una fila con meteorología y PM2.5) | Una entidad «Observación» con las 4 variables | Las fuentes tienen pasos (1 h frente a 3 h), latencias (5 días frente a horas) y lotes distintos. Una fila combinada estaría a medio llenar casi siempre y no permitiría saber qué lote aportó cada valor. |
| **Persistir las franjas** | Una entidad con los promedios por franja | Es un dato derivado: si cambia la regla (D-009 está pendiente de revisión), habría que recalcular y migrar. Consumiría además una de las 10 clases gratuitas. Calcularlas en Python es barato (D-021). |
| Python lee el `.odb` directamente | — | No es un formato documentado y la licencia prohíbe la ingeniería inversa [Verificado: [ObjectDB – licencia](https://www.objectdb.com/database/license)]. |

## Estructura de directorios prevista

Esta es la **estructura planificada**; todavía no existe nada salvo `docs/` y `README.md`.

```text
clima-medellin/
├── README.md
├── docs/                 documentación (este conjunto de .md)
├── python/               CLI, cliente HTTP, normalización, cobertura, franjas,
│                         estadística, regresión y visualizaciones
├── java/                 proyecto Java: entidades JPA y subcomandos del JAR
├── data/                 archivo .odb de ObjectDB (no se versiona)
├── staging/              lotes .jsonl de Python hacia Java (temporal, no se versiona)
├── exchange/             exportaciones .jsonl de Java hacia Python (temporal, no se versiona)
├── samples/              respuestas de las APIs guardadas en la Fase 1
└── outputs/              gráficas PNG generadas
```

La organización interna de `python/` y `java/` (módulos, paquetes, herramienta de construcción) se decide en las fases 2–4.

## Fuentes consultadas

- ObjectDB, Download: https://www.objectdb.com/download
- ObjectDB, License: https://www.objectdb.com/database/license
- ObjectDB, Purchase (límites de la versión gratuita): https://www.objectdb.com/database/purchase
- ObjectDB Manual, conexión: https://www.objectdb.com/java/jpa/start/connection
- ObjectDB Manual, claves primarias: https://www.objectdb.com/java/jpa/entity/id
- ObjectDB Manual, índices: https://www.objectdb.com/java/jpa/entity/index

## Limitaciones y supuestos

- Los campos y los tipos de las entidades quedaron fijados en la Fase 2 (`java/src/main/java/co/climamedellin/entities/`).
- La creación del archivo, el índice único y el comportamiento ante duplicados se verificaron en la Fase 2 con las pruebas de `RecordStoreTest`.
- Se supone un único usuario y un único proceso Java a la vez. Si un proceso tiene el `.odb` abierto, un segundo proceso falla de inmediato con «currently in use by another process» (código 3) [Verificado: PV-15, Fase 4]; no hay espera ni reintento.
- El coste de arrancar la JVM en cada subcomando se considera aceptable sin haberlo medido [Supuesto].
