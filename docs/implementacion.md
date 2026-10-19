# Guía técnica de la implementación

Este documento explica **cómo está construido el código**: las llamadas a ObjectDB, la inserción y la consulta de datos, los *joins*, el envío de datos de ObjectDB a Python, el análisis y las gráficas. Complementa a [arquitectura.md](arquitectura.md), que explica el **qué** y el **porqué**; aquí se explica el **cómo**, con ejemplos.

Cada especificación del proyecto añade su sección cuando construye la parte correspondiente, así que el documento crece junto con el código.

## Cómo leer este documento

Cada tema sigue siempre el mismo formato:

1. **Concepto**: qué es y por qué lo usa el proyecto, en 2–4 frases.
2. **Sintaxis básica**: un ejemplo mínimo e independiente, para entender la forma general.
3. **En este proyecto**: un fragmento real del código, con la ruta del archivo, y su explicación línea a línea.
4. **Cuidado**: el error típico que el código evita.

## Convención de fragmentos

Los fragmentos reales se marcan con un comentario HTML justo antes del bloque de código:

````text
<!-- fragmento: java/src/main/java/co/climamedellin/cli/Main.java -->
```java
...código copiado literalmente...
```
````

- La ruta es relativa a la raíz del repositorio.
- El código se copia **literalmente** y **sin omisiones** (nada de `...` dentro de un fragmento real).
- La prueba `python/tests/test_docs_excerpts.py` comprueba que cada fragmento marcado sigue apareciendo tal cual en su archivo (ignorando los espacios al final de cada línea). Si alguien cambia el código y no actualiza este documento, la prueba falla y la integración continua lo detecta.
- Los ejemplos de **Sintaxis básica** no llevan la marca: son ilustrativos y no proceden del proyecto.

## Compilar, probar y ejecutar

| Acción | Comando (desde la raíz del repositorio) |
|---|---|
| Instalar | `cd java && mvn -q -DskipTests package && cd ../python && uv sync` |
| Probar | `cd java && mvn -q verify && cd ../python && uv run pytest` |
| Analizar el estilo (Python) | `cd python && uv run ruff check .` |
| Compilar el JAR | `cd java && mvn -q -DskipTests package` |
| Ejecutar la CLI | `cd python && uv run clima-medellin` |
| Ejecutar el JAR a mano | `java -jar java/target/clima-medellin.jar <subcomando> [opciones]` |

- **Maven** compila el proyecto Java y, con el plugin *shade*, genera un único JAR (`java/target/clima-medellin.jar`) que lleva dentro ObjectDB, la API de JPA y Jackson. Así Python lo ejecuta con un solo comando, sin gestionar el *classpath*.
- **uv** crea el entorno virtual de Python (`python/.venv`), instala las dependencias fijadas en `python/uv.lock` y registra el comando `clima-medellin`.
- La integración continua (`.github/workflows/ci.yml`) ejecuta los mismos comandos de instalación, prueba y análisis en cada pull request.

## Índice

| Sección | Estado | Especificación |
|---|---|---|
| [1. Punto de entrada del JAR y contrato de salida](#1-punto-de-entrada-del-jar-y-contrato-de-salida) | Disponible | `project-scaffold` |
| [2. ObjectDB: entidades, transacciones, inserción y consultas JPQL](#2-objectdb-entidades-transacciones-inserción-y-consultas-jpql) | Disponible | `persistence` |
| [3. Descarga de Open-Meteo y normalización con Pandas](#3-descarga-de-open-meteo-y-normalización-con-pandas) | Disponible | `ingest` |
| [4. Puente Java↔Python: subprocesos, JSON Lines y de ObjectDB a Python](#4-puente-javapython-subprocesos-json-lines-y-de-objectdb-a-python) | Disponible | `bridge` |
| [5. Ventana móvil, cobertura e intervalos faltantes](#5-ventana-móvil-cobertura-e-intervalos-faltantes) | Disponible | `coverage` |
| [6. Zonas horarias, franjas y estadística descriptiva](#6-zonas-horarias-franjas-y-estadística-descriptiva) | Disponible | `bands-stats` |
| 7. Unión de datos, split temporal y regresión | Pendiente | `regression` |
| 8. Gráficas con Matplotlib | Pendiente | `visualizations` |
| 9. Menú de la CLI | Pendiente | `cli-integration` |

---

## 1. Punto de entrada del JAR y contrato de salida

### 1.1 El método `main` y el código de salida

**Concepto.** Un JAR ejecutable arranca en el método `public static void main(String[] args)` de la clase indicada en su manifiesto. Cuando el programa termina, el sistema operativo recibe un **código de salida**: 0 significa éxito y cualquier otro número, un tipo de fallo. Python lee ese código para saber qué pasó sin tener que interpretar texto.

**Sintaxis básica.**

```java
public class Hola {
    public static void main(String[] args) {
        System.out.println("Hola, " + args[0]);
        System.exit(0); // 0 = todo fue bien
    }
}
```

`java -jar hola.jar Medellín` imprime `Hola, Medellín` y termina con código 0. En la terminal, `echo $?` muestra el código de la última orden.

**En este proyecto.**

<!-- fragmento: java/src/main/java/co/climamedellin/cli/Main.java -->
```java
    public static void main(String[] args) {
        System.exit(run(args, System.out, System.err));
    }
```

- `main` no hace nada por sí mismo: delega en `run(...)`, que recibe los argumentos y los dos canales de salida (`System.out` para stdout y `System.err` para stderr).
- `run` devuelve el código de salida y `System.exit(...)` se lo entrega al sistema operativo.
- Separar `run` de `main` permite que las pruebas JUnit llamen a `run` con canales falsos y comprueben la salida y el código **sin lanzar un proceso** ni terminar la JVM de las pruebas.

**Cuidado.** Llamar a `System.exit` dentro de la lógica (en lugar de devolver el código) haría imposible probarla: la prueba terminaría la JVM entera.

### 1.2 Un único objeto JSON por stdout

**Concepto.** Python y Java se comunican por procesos ([arquitectura.md](arquitectura.md#protocolo-de-comunicación)). Para que Python pueda leer la respuesta sin ambigüedad, el JAR escribe en stdout **exactamente un objeto JSON** y nada más; los mensajes de registro van a stderr. Los errores usan siempre el mismo sobre: `{"ok": false, "error": {"type": ..., "message": ...}}`.

**Sintaxis básica.** Con Jackson, un objeto JSON se construye como un árbol de nodos:

```java
ObjectMapper mapper = new ObjectMapper();
ObjectNode respuesta = mapper.createObjectNode();
respuesta.put("ok", true);
respuesta.put("insertados", 744);
System.out.println(respuesta.toString()); // {"ok":true,"insertados":744}
```

**En este proyecto.**

<!-- fragmento: java/src/main/java/co/climamedellin/cli/Main.java -->
```java
    static int fail(PrintStream out, int exitCode, String type, String message) {
        ObjectNode response = MAPPER.createObjectNode();
        response.put("ok", false);
        ObjectNode error = response.putObject("error");
        error.put("type", type);
        error.put("message", message);
        out.println(response.toString());
        return exitCode;
    }
```

- `MAPPER.createObjectNode()` crea el objeto JSON vacío de la respuesta.
- `putObject("error")` crea un objeto anidado y lo devuelve para rellenarlo con el tipo y el mensaje.
- `out.println(response.toString())` escribe el JSON **en una sola línea**, que es lo que Python espera leer.
- El método devuelve el código de salida para que quien lo llama haga `return fail(...)` en una sola línea.

El tipo de error y el código de salida van siempre juntos (DP-05):

| `error.type` | Código | Significado |
|---|---|---|
| — | 0 | Éxito |
| `USAGE` | 1 | Subcomando o argumentos inválidos |
| `DATA` | 2 | Archivo inexistente, línea JSON inválida o violación de esquema |
| `DATABASE` | 3 | No se puede abrir la base, está bloqueada o falla una transacción |
| `UNEXPECTED` | 4 | Error inesperado |

Ejemplo real de ejecución:

```text
$ java -jar java/target/clima-medellin.jar foo
{"ok":false,"error":{"type":"USAGE","message":"Subcomando desconocido: foo"}}
$ echo $?
1
```

**Cuidado.** Un `System.out.println("Procesando...")` olvidado en cualquier parte del código Java rompería la respuesta: stdout dejaría de ser un único JSON. Todo mensaje de progreso debe ir a stderr.

---

## 2. ObjectDB: entidades, transacciones, inserción y consultas JPQL

Las clases están en `java/src/main/java/co/climamedellin/entities/` (qué se guarda) y `java/src/main/java/co/climamedellin/persistence/` (cómo se guarda y se consulta). Las pruebas que demuestran cada comportamiento están en `java/src/test/java/co/climamedellin/persistence/RecordStoreTest.java`.

### 2.1 Abrir la base: `EntityManagerFactory` y `EntityManager`

**Concepto.** JPA (*Jakarta Persistence*) es la API estándar de Java para guardar objetos en una base de datos. Se trabaja con dos objetos: la **`EntityManagerFactory`** representa la base abierta (se crea una vez y es costosa) y cada **`EntityManager`** es una sesión de trabajo corta (se crea por operación y se cierra). Con ObjectDB, la base es un único archivo `.odb` y basta una URL `objectdb:<ruta>` para abrirla; si el archivo no existe, se crea.

**Sintaxis básica.**

```java
EntityManagerFactory emf = Persistence.createEntityManagerFactory("objectdb:data/ejemplo.odb");
EntityManager em = emf.createEntityManager();
// ... operaciones ...
em.close();
emf.close();
```

**En este proyecto.**

<!-- fragmento: java/src/main/java/co/climamedellin/persistence/Database.java -->
```java
        EntityManagerFactory emf =
                Persistence.createEntityManagerFactory("objectdb:" + file.toAbsolutePath());
        // ObjectDB solo conoce una clase cuando se guarda su primer objeto; registrarlas
        // al abrir permite consultar una entidad aunque todavía no tenga registros. El
        // registro se hace desde un EntityManager porque es él quien abre el archivo.
        EntityManager em = emf.createEntityManager();
        try {
            for (Class<?> entityClass : ENTITY_CLASSES) {
                em.getMetamodel().entity(entityClass);
            }
        } finally {
            em.close();
        }
        return new Database(emf);
```

- `Persistence.createEntityManagerFactory("objectdb:" + ruta)` abre (o crea) el archivo. No hace falta `persistence.xml`.
- `em.getMetamodel().entity(clase)` registra cada una de las cuatro entidades en el esquema de la base. Sin esto, una consulta como `SELECT COUNT(r) FROM WeatherRecord r` sobre una base recién creada falla con *«Type WeatherRecord is not found»*, porque ObjectDB todavía no ha visto ningún objeto de esa clase.
- `Database` implementa `AutoCloseable`, así que se puede usar con `try (Database db = Database.open(ruta)) { ... }` y se cierra sola.

**Cuidado.** El registro debe hacerse desde un `EntityManager` (que es quien abre realmente el archivo). Registrar desde la fábrica, antes de crear ningún `EntityManager`, no tiene efecto: se comprobó durante la implementación.

### 2.2 Entidades y anotaciones

**Concepto.** Una **entidad** es una clase Java cuyos objetos se guardan en la base. Se marca con `@Entity` y necesita un identificador (`@Id`). Las relaciones entre entidades se declaran con anotaciones como `@ManyToOne` («muchos registros apuntan a una ubicación»).

**Sintaxis básica.**

```java
@Entity
public class Libro {
    @Id @GeneratedValue
    private long id;          // identificador técnico generado por la base
    private String titulo;
    @ManyToOne
    private Autor autor;      // muchos libros, un autor
    protected Libro() { }     // JPA exige un constructor sin argumentos
}
```

**En este proyecto.**

<!-- fragmento: java/src/main/java/co/climamedellin/entities/WeatherRecord.java -->
```java
@Entity
@Unique(members = {"location", "source", "timestampUtc"})
public class WeatherRecord {

    @Id
    @GeneratedValue
    private long id;

    @ManyToOne
    private Location location;

    @Enumerated(EnumType.STRING)
    private Source source;

    /** Instante UTC del dato (D-008). */
    private Instant timestampUtc;

    private Double temperature2mC;
    private Double relativeHumidity2mPct;
    private Double windSpeed10mMs;
```

- `@Id @GeneratedValue`: id técnico que asigna ObjectDB. La clave «de negocio» es otra (ver 2.3).
- `@ManyToOne private Location location`: cada registro apunta a una ubicación; en la base se guarda la referencia, no una copia.
- `@Enumerated(EnumType.STRING)`: la fuente (`ERA5` o `CAMS_GLOBAL`) se guarda como texto, legible y estable aunque se reordene el enum.
- `Instant timestampUtc`: un instante absoluto en UTC. Se comprobó que vuelve exactamente igual aunque la JVM que lee esté en otra zona horaria (PV-14).
- `Double` y no `double`: el tipo envoltorio admite `null`, que significa «no hay dato» (D-012). Un `double` primitivo no puede ser `null` y obligaría a inventar un 0.

El proyecto tiene 4 entidades (`Location`, `WeatherRecord`, `AirQualityRecord`, `IngestionBatch`), muy por debajo del límite de 10 de la versión gratuita. `Source` y `BatchType` son enums, no entidades.

**Cuidado.** Si `temperature2mC` fuera `double`, un valor ausente se guardaría como `0.0` y la media de temperatura bajaría sin que nadie lo notara.

### 2.3 Clave natural única con `@Unique`

**Concepto.** Además del id técnico, cada registro tiene una **clave natural**: la combinación (ubicación, fuente, timestamp) que lo identifica en el mundo real. Un **índice único** hace que la base rechace un segundo objeto con la misma combinación, aunque el código que inserta se equivoque (D-011).

**Sintaxis básica.**

```java
@Entity
@Unique(members = {"pais", "numero"})   // no puede haber dos pasaportes con el mismo país y número
public class Pasaporte { ... }
```

**En este proyecto.** La anotación aparece en la primera línea del fragmento de 2.2: `@Unique(members = {"location", "source", "timestampUtc"})`. Es `javax.jdo.annotations.Unique`, que viene incluida en el JAR de ObjectDB. Se comprobó que el índice admite el campo de relación `location` (PV-13), así que no hace falta copiar el código de la ubicación en cada registro.

La prueba `databaseRejectsADuplicateNaturalKeyEvenWithoutTheService` persiste un duplicado directamente, sin pasar por el servicio, y comprueba que `commit()` lanza una `PersistenceException` y que la base sigue con un solo registro.

**Cuidado.** La violación del índice se detecta **al confirmar** la transacción, no al llamar a `persist`. Si un lote de 500 registros contiene un duplicado, la transacción entera se deshace. Por eso el servicio comprueba antes qué claves existen (2.5).

### 2.4 Transacciones y `persist`

**Concepto.** Una **transacción** agrupa cambios que se guardan todos o ninguno. Con JPA: `begin()`, operaciones, `commit()`; si algo falla, `rollback()` deshace lo pendiente. `persist(objeto)` marca un objeto nuevo para guardarlo en el siguiente `commit`.

**Sintaxis básica.**

```java
em.getTransaction().begin();
em.persist(new Libro("Cien años de soledad"));
em.getTransaction().commit();   // aquí se escribe en el archivo
```

**En este proyecto.** Asegurar la ubicación: si el código existe se devuelve; si no, se guarda en una transacción.

<!-- fragmento: java/src/main/java/co/climamedellin/persistence/RecordStore.java -->
```java
            List<Location> found = em.createQuery(
                            "SELECT l FROM Location l WHERE l.code = :code", Location.class)
                    .setParameter("code", data.code())
                    .getResultList();
            if (!found.isEmpty()) {
                return found.get(0);
            }
            Location location = new Location(data.code(), data.name(), data.latitude(),
                    data.longitude(), data.elevationM(), data.timezone());
            em.getTransaction().begin();
            em.persist(location);
            em.getTransaction().commit();
            return location;
```

- `createQuery(jpql, Location.class)` crea una consulta tipada: el resultado es una `List<Location>`.
- `:code` es un **parámetro con nombre**; `setParameter("code", ...)` le da valor. Nunca se concatena el valor en el texto de la consulta.
- Si no hay resultados, se crea la `Location` y se guarda con `begin` / `persist` / `commit`.

**Cuidado.** Olvidar `commit()` deja el objeto sin guardar: al cerrar el `EntityManager`, el cambio se pierde.

### 2.5 Insertar un lote: duplicados y bloques de 500

**Concepto.** Guardar un lote sigue el principio de «solo inserciones» (D-013): lo que ya existe no se toca. El algoritmo de `RecordStore.insert`: (1) guarda el `IngestionBatch`; (2) rechaza filas sin timestamp o con todo a `null`; (3) carga en un `Set<Instant>` los timestamps que ya existen en el rango del lote; (4) descarta como duplicado cada fila cuyo timestamp ya esté en el conjunto (de la base o del propio lote); (5) inserta el resto en transacciones de como máximo 500 registros.

**Sintaxis básica.** El patrón «comprobar con un conjunto» en Java:

```java
Set<Instant> vistos = new HashSet<>(existentesEnLaBase);
for (Fila f : filas) {
    if (vistos.add(f.timestamp())) {   // add devuelve false si ya estaba
        pendientes.add(f);
    } else {
        duplicados++;
    }
}
```

**En este proyecto.** La confirmación de un bloque:

<!-- fragmento: java/src/main/java/co/climamedellin/persistence/RecordStore.java -->
```java
        EntityTransaction tx = em.getTransaction();
        try {
            tx.begin();
            Context ctx = managedContext(em, location, batchId);
            for (V row : block) {
                em.persist(toEntity.apply(row, ctx));
            }
            tx.commit();
            return block.size();
        } catch (PersistenceException e) {
            if (tx.isActive()) {
                tx.rollback();
            }
            return 0;
        } finally {
            // Se vacía el contexto para no acumular miles de objetos en memoria.
            em.clear();
        }
```

- `managedContext(...)` vuelve a obtener con `em.find` la ubicación y el lote, porque `em.clear()` del bloque anterior los «desconectó» del `EntityManager`.
- `toEntity.apply(row, ctx)` convierte cada fila de entrada (un `record` de Java) en una entidad `WeatherRecord` o `AirQualityRecord`.
- Si `commit()` falla, `rollback()` deshace solo ese bloque y el servicio reintenta sus registros uno a uno; los que vuelvan a fallar cuentan como rechazados. Los bloques ya confirmados no se pierden.
- La prueba `largeBatchIsCommittedInBlocksOf500` inserta 1 200 registros y comprueba que se confirman en 3 bloques.

**Cuidado.** Sin `em.clear()`, el `EntityManager` guarda en memoria todos los objetos que ha visto; con un año de datos (8 760 registros) por fuente sigue funcionando, pero es una fuga de memoria innecesaria.

### 2.6 Consultas JPQL con `JOIN`

**Concepto.** JPQL es el lenguaje de consultas de JPA. Se parece a SQL, pero trabaja con **clases y campos** en lugar de tablas y columnas. Un `JOIN` recorre una relación: `JOIN r.location l` permite filtrar los registros por un campo de su ubicación.

**Sintaxis básica.**

```sql
SELECT b FROM Libro b JOIN b.autor a WHERE a.nombre = :nombre ORDER BY b.titulo
```

**En este proyecto.**

<!-- fragmento: java/src/main/java/co/climamedellin/persistence/RecordStore.java -->
```java
            String jpql = "SELECT r FROM " + entityClass.getSimpleName() + " r"
                    + " JOIN r.location l"
                    + " WHERE l.code = :code AND r.timestampUtc >= :from AND r.timestampUtc < :to"
                    + " ORDER BY r.timestampUtc";
            return em.createQuery(jpql, entityClass)
                    .setParameter("code", locationCode)
                    .setParameter("from", from)
                    .setParameter("to", to)
                    .getResultList();
```

- `entityClass.getSimpleName()` es `WeatherRecord` o `AirQualityRecord`: la misma consulta sirve para las dos entidades. Es seguro concatenarlo porque es el nombre de una clase del propio programa, no un dato del usuario.
- `JOIN r.location l WHERE l.code = :code` filtra por el código de la ubicación (`MED-CENTRO`).
- El rango es **semiabierto** `[from, to)`: incluye `from` y excluye `to`, así dos rangos consecutivos no repiten la hora del borde.
- `ORDER BY r.timestampUtc` devuelve los registros en orden cronológico aunque se insertaran desordenados.

**Cuidado.** Usar `<=` en el extremo final haría que la hora `to` apareciera en dos consultas consecutivas.

### 2.7 Agregaciones: `COUNT`, `MIN`, `MAX`

**Concepto.** Las funciones de agregación resumen muchos registros en un valor. En JPQL, `COUNT(r)` cuenta registros y `COUNT(r.campo)` cuenta solo los que tienen ese campo **no nulo**; así se sabe cuántos valores reales hay de cada variable sin descargar los registros.

**Sintaxis básica.**

```sql
SELECT COUNT(b), MIN(b.anio), MAX(b.anio) FROM Libro b
```

**En este proyecto.**

<!-- fragmento: java/src/main/java/co/climamedellin/persistence/RecordStore.java -->
```java
        Object[] row = aggregate("SELECT COUNT(r), COUNT(r.temperature2mC),"
                + " COUNT(r.relativeHumidity2mPct), COUNT(r.windSpeed10mMs),"
                + " MIN(r.timestampUtc), MAX(r.timestampUtc)"
                + " FROM WeatherRecord r JOIN r.location l WHERE l.code = :code", locationCode);
```

- La consulta devuelve una sola fila con 6 columnas, que JPA entrega como `Object[]`.
- Si hay 3 registros y uno tiene la humedad a `null`, `COUNT(r)` vale 3 y `COUNT(r.relativeHumidity2mPct)` vale 2 (prueba `summaryCountsRecordsNonNullValuesAndBounds`).
- Con la base vacía, los conteos valen 0 y `MIN`/`MAX` devuelven `null`.

**Cuidado.** `COUNT(*)` no existe en JPQL; se escribe `COUNT(r)` con la variable de la entidad.

---

## 3. Descarga de Open-Meteo y normalización con Pandas

El código está en `python/src/clima_medellin/`: `config.py` (ubicación, fuentes, unidades y rangos), `openmeteo.py` (peticiones HTTP) y `normalize.py` (de JSON a tabla). Las pruebas `test_openmeteo.py` y `test_normalize.py` no usan la red: el cliente se prueba con una sesión falsa y la normalización con las respuestas reales de `samples/`.

### 3.1 Petición HTTP con `requests`

**Concepto.** Una API REST se consulta con una petición HTTP GET a una URL con **parámetros de consulta** (`?latitude=6.2447&models=era5...`). La biblioteca `requests` construye la URL a partir de un diccionario y devuelve una respuesta con su **código de estado** (200 = correcto, 4xx = la petición está mal, 5xx = fallo del servidor) y su cuerpo JSON.

**Sintaxis básica.**

```python
import requests

respuesta = requests.get(
    "https://archive-api.open-meteo.com/v1/archive",
    params={"latitude": 6.2447, "longitude": -75.5748, "start_date": "2026-03-01",
            "end_date": "2026-03-01", "hourly": "temperature_2m"},
    timeout=60,                      # sin timeout, una red caída bloquea el programa
)
print(respuesta.status_code)         # 200
datos = respuesta.json()             # dict de Python
```

**En este proyecto.** Los parámetros fijos de cada fuente están en `config.py` (`models=era5`, `elevation=1495`, `wind_speed_unit=ms` para ERA5; `domains=cams_global` para PM2.5) y `build_request` les añade el rango de fechas:

<!-- fragmento: python/src/clima_medellin/openmeteo.py -->
```python
    config = SOURCES[source]
    params = {
        **config.fixed_params,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    return config.url, params
```

- `SOURCES[source]` elige la configuración de `"ERA5"` o `"CAMS_GLOBAL"` (los mismos nombres que el enum `Source` de Java).
- `{**config.fixed_params, ...}` copia los parámetros fijos y añade las fechas sin modificar el diccionario original.
- `start.isoformat()` convierte una fecha en texto `aaaa-mm-dd`, que es lo que espera la API. Las fechas son **inclusivas**: `end_date=2026-03-31` incluye todo el día 31.

**Cuidado.** La Air Quality API no documenta el parámetro `elevation`, por eso solo aparece en los parámetros de ERA5.

### 3.2 Reintentos ante fallos transitorios

**Concepto.** Una red o un servidor pueden fallar un momento. Reintentar con **espera creciente** (1 s, 2 s, 4 s) da tiempo a que se recuperen sin saturarlos. Solo tiene sentido reintentar los fallos transitorios (tiempo agotado, conexión caída, 5xx); un 4xx significa que la petición está mal y repetirla daría el mismo error.

**Sintaxis básica.**

```python
for intento in range(4):
    try:
        r = requests.get(url, timeout=60)
        if r.status_code < 500:
            break                    # éxito o error definitivo: no se reintenta
    except requests.Timeout:
        pass
    time.sleep(2 ** intento)         # 1, 2, 4, 8 segundos
```

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/openmeteo.py -->
```python
    for attempt in range(len(RETRY_DELAYS_S) + 1):
        if attempt > 0:
            sleep(RETRY_DELAYS_S[attempt - 1])
        try:
            response = http.get(url, params=params, timeout=TIMEOUT_S)
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_problem = type(exc).__name__
            continue
        if response.status_code >= 500:
            last_problem = f"HTTP {response.status_code}"
            continue
        if response.status_code != 200:
            raise OpenMeteoError(f"{label}: la API respondió HTTP {response.status_code}")
        return response.json()
```

- `RETRY_DELAYS_S = (1, 2, 4)`: 1 intento inicial + 3 reintentos, con esperas de 1, 2 y 4 s.
- `continue` salta al siguiente intento ante un fallo transitorio; un estado distinto de 200 y menor que 500 lanza `OpenMeteoError` en el acto.
- `sleep` y `http` (la sesión) se reciben como parámetros: en las pruebas se pasa una sesión falsa que devuelve 503, 503 y 200, y una función que solo anota las esperas, así la prueba comprueba `[1, 2]` sin esperar de verdad.
- Si se agotan los intentos, el error menciona la fuente y el rango (`ERA5 2026-03-01 → 2026-03-31`), para saber qué intervalo reintentar.

**Cuidado.** Reintentar un 400 (por ejemplo, una fecha mal escrita) solo retrasaría el error tres veces.

### 3.3 De JSON a DataFrame con índice UTC

**Concepto.** Open-Meteo devuelve **listas paralelas**: `hourly.time` con las horas y una lista por variable con los valores en el mismo orden. Un **DataFrame** de Pandas las convierte en una tabla con un **índice temporal**. Como las horas llegan en GMT **sin sufijo de zona** (`"2026-03-01T13:00"`), hay que decirle a Pandas explícitamente que son UTC.

**Sintaxis básica.**

```python
import pandas as pd

horas = ["2026-03-01T13:00", "2026-03-01T14:00"]
temperaturas = [21.4, None]
indice = pd.to_datetime(horas, utc=True)          # 2026-03-01 13:00:00+00:00, ...
tabla = pd.DataFrame({"temperature_2m_c": temperaturas}, index=indice)
#                            temperature_2m_c
# 2026-03-01 13:00:00+00:00              21.4
# 2026-03-01 14:00:00+00:00               NaN
```

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/normalize.py -->
```python
    # Las horas llegan en GMT sin sufijo de zona: se interpretan explícitamente como UTC.
    index = pd.DatetimeIndex(pd.to_datetime(hourly["time"], utc=True), name="timestamp_utc")
    frame = pd.DataFrame(
        {
            v.column: pd.to_numeric(pd.Series(hourly[v.api_name]), errors="coerce").to_numpy(float)
            for v in config.variables
        },
        index=index,
    )
```

- `pd.to_datetime(..., utc=True)` crea timestamps **con zona** UTC. Sin `utc=True` serían «ingenuos» (sin zona) y una conversión posterior a hora de Medellín sería ambigua.
- El diccionario por comprensión crea una columna por variable con su **nombre canónico** (`temperature_2m` → `temperature_2m_c`, `pm2_5` → `pm25_ug_m3`), que lleva la unidad en el nombre (D-022).
- `pd.to_numeric(..., errors="coerce")` y `.to_numpy(float)` convierten los `None` del JSON en `NaN`, el «no hay dato» de Pandas (D-012).

**Cuidado.** `pd.to_datetime(horas)` sin `utc=True` no da error, pero produce horas sin zona: el fallo aparecería mucho después, al calcular la franja de la noche, que en UTC cae en el día siguiente.

### 3.4 Validar sin inventar valores: `where`, duplicados y recortes

**Concepto.** Validar es detectar lo imposible (una humedad de 140 %) **sin sustituirlo por un valor inventado**: el valor pasa a `NaN` y se cuenta. Antes de guardar también se eliminan los timestamps repetidos, lo que queda en o después del fin efectivo de la fuente y las filas sin ningún dato (DP-12).

**Sintaxis básica.**

```python
s = pd.Series([21.0, 80.0, None])
valido = s.isna() | s.between(-20, 50)   # True donde el valor es plausible o ya falta
s = s.where(valido)                      # donde valido es False, pone NaN
# [21.0, NaN, NaN]
```

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/normalize.py -->
```python
    for variable in config.variables:
        column = frame[variable.column]
        plausible = column.isna() | column.between(variable.minimum, variable.maximum)
        report.out_of_range[variable.column] = int((~plausible).sum())
        frame[variable.column] = column.where(plausible)

    duplicated = frame.index.duplicated(keep="first")
    report.duplicates = int(duplicated.sum())
    frame = frame[~duplicated]
```

- Los rangos plausibles están en `config.py`: temperatura −20..50 °C, humedad 0..100 %, viento 0..75 m/s y PM2.5 0..1000 µg/m³. Son amplios a propósito: solo atrapan valores imposibles.
- `~plausible` invierte la máscara; su suma es el número de valores fuera de rango, que queda en el informe.
- `index.duplicated(keep="first")` marca las repeticiones de un timestamp salvo la primera; `frame[~duplicated]` se queda con el resto.
- Después, `frame.index >= end` elimina lo que está en o después del fin efectivo (las horas de ERA5 aún no publicadas llegan como `null`), y `frame.isna().all(axis=1)` encuentra las filas en las que **todas** las variables son `NaN`, que se descartan.

Ejemplo real con la muestra anual de ERA5 descargada el 2026-10-18: llegan 8 760 horas, 96 están en o después del fin efectivo (00:00 UTC del 2026-10-14) y quedan **8 664 filas**, todas con datos.

**Cuidado.** Rellenar los huecos con 0 (`fillna(0)`) haría que una hora sin viento medido pareciera una hora de calma total, y bajaría la media del viento.

---

## 4. Puente Java↔Python: subprocesos, JSON Lines y de ObjectDB a Python

Python nunca abre el archivo `.odb` (D-002): le pide a Java cada operación ejecutando el JAR como **proceso hijo**. El lado Java está en `java/src/main/java/co/climamedellin/cli/` (`Main`, `Options`, `ImportCommand`, `CoverageCommand`, `ExportCommand`, `JsonLines`) y el lado Python en `python/src/clima_medellin/bridge.py` y `jsonlines.py`.

```text
 Python (bridge.py)                                Java (clima-medellin.jar)
 ------------------                                -------------------------
 DataFrame --write_frame--> staging/ERA5-...jsonl
 subprocess.run(["java","-jar",...,"import",...]) --> ImportCommand: valida, RecordStore.insert...
                 <-- stdout: {"ok":true,"inserted":744,...}   código 0
 subprocess.run([... "export" ...])               --> ExportCommand: findWeather(...) --> exchange/export-ERA5.jsonl
                 <-- stdout: {"ok":true,"file":...,"lines":744}
 read_frame(exchange/export-ERA5.jsonl) --> DataFrame
```

### 4.1 Ejecutar el JAR como proceso hijo con `subprocess`

**Concepto.** Un **proceso hijo** es otro programa que Python lanza y espera. Se comunican por tres canales: los **argumentos** (lo que Python le pide), **stdout** (la respuesta, un único JSON) y **stderr** (mensajes de registro), más el **código de salida** (0 = éxito). `subprocess.run` con `capture_output=True` guarda stdout y stderr en lugar de mostrarlos.

**Sintaxis básica.**

```python
import subprocess

r = subprocess.run(["java", "-version"], capture_output=True, text=True)
print(r.returncode)   # 0
print(r.stderr)       # java -version escribe en stderr
```

Los argumentos se pasan como **lista**, no como una cadena para la shell: así un valor con espacios o comillas (por ejemplo, el JSON de `--meta`) llega intacto.

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/bridge.py -->
```python
        command = [
            self.java,
            # Silencia el aviso de sun.misc.Unsafe que ObjectDB provoca en Java 25.
            "--sun-misc-unsafe-memory-access=allow",
            "-jar",
            str(self.jar),
            *args,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if self.verbose and completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        lines = completed.stdout.strip().splitlines()
```

- `*args` añade el subcomando y sus opciones, por ejemplo `"export", "--db", "data/clima.odb", "--location", "MED-CENTRO", ...`.
- `encoding="utf-8"` garantiza que las tildes de los mensajes de Java (`«Línea 2: no es un JSON válido»`) lleguen bien.
- En modo detallado (`verbose=True`) el stderr de Java se reenvía al stderr de Python; si no, se oculta.

**Cuidado.** Lanzar el JAR con `shell=True` y una sola cadena obligaría a escapar las comillas del JSON de `--meta`; con una lista no hace falta.

### 4.2 El contrato: un JSON por stdout y un código de salida

**Concepto.** El JAR responde siempre con **un único objeto JSON en una línea** de stdout y termina con un código que clasifica el resultado (DP-05). Python primero interpreta el JSON y después mira el código para decidir si es un éxito o un error y qué mensaje mostrar.

**Sintaxis básica.**

```python
import json
respuesta = json.loads('{"ok": false, "error": {"type": "DATA", "message": "Línea 2: ..."}}')
respuesta["error"]["type"]   # 'DATA'
```

**En este proyecto (Java).** `Main` traduce cada tipo de excepción a un código:

<!-- fragmento: java/src/main/java/co/climamedellin/cli/Main.java -->
```java
        } catch (UsageException e) {
            return fail(out, EXIT_USAGE, "USAGE", e.getMessage());
        } catch (DataException e) {
            return fail(out, EXIT_DATA, "DATA", e.getMessage());
        } catch (PersistenceException e) {
            e.printStackTrace(err);
            return fail(out, EXIT_DATABASE, "DATABASE",
                    "No se pudo usar la base de datos: " + firstLine(e.getMessage()));
        } catch (RuntimeException e) {
            e.printStackTrace(err);
            return fail(out, EXIT_UNEXPECTED, "UNEXPECTED",
                    e.getClass().getSimpleName() + ": " + firstLine(e.getMessage()));
        }
```

**En este proyecto (Python).** `bridge.py` exige una sola línea y traduce el código:

<!-- fragmento: python/src/clima_medellin/bridge.py -->
```python
        if completed.returncode != 0:
            error = response.get("error", {})
            text = EXIT_MESSAGES.get(completed.returncode, "Error del JAR")
            raise BridgeError(
                f"{text}: {error.get('message', '')}",
                exit_code=completed.returncode,
                error_type=error.get("type"),
            )
        return response
```

| Código | `error.type` | Cuándo | Mensaje en Python |
|---|---|---|---|
| 0 | — | Éxito (los duplicados omitidos no son error) | — |
| 1 | `USAGE` | Subcomando u opción desconocidos, opción sin valor, fuente inválida | «Error de uso del JAR…» |
| 2 | `DATA` | Archivo inexistente, línea que no es JSON, timestamp sin `Z`, valor no numérico, fuente distinta | «El lote tiene datos inválidos: Línea N…» |
| 3 | `DATABASE` | La base no se puede abrir (por ejemplo, otro proceso la tiene abierta) o falla una transacción | «No se pudo usar la base de datos; cierra otras ejecuciones…» |
| 4 | `UNEXPECTED` | Cualquier otro error | «Error inesperado en el programa Java…» |

Las trazas de las excepciones (`printStackTrace(err)`) van a stderr: solo se ven en modo detallado.

**Cuidado.** El caso 3 no es teórico: se comprobó que, si un proceso tiene el `.odb` abierto, un segundo proceso falla de inmediato con «Attempt to open a database file … that is currently in use by another process» (PV-15). Por eso la aplicación asume una sola ejecución a la vez.

### 4.3 JSON Lines: un registro por línea

**Concepto.** **JSON Lines** es un archivo de texto en el que **cada línea es un objeto JSON completo** (D-004). Se puede leer y validar línea a línea, un error indica su número de línea exacto y los ausentes se escriben como `null` (algo que CSV no distingue de una celda vacía).

**Sintaxis básica.**

```text
{"location_code":"MED-CENTRO","source":"ERA5","timestamp_utc":"2026-03-01T13:00:00Z","temperature_2m_c":21.4,"relative_humidity_2m_pct":78.0,"wind_speed_10m_ms":null}
{"location_code":"MED-CENTRO","source":"ERA5","timestamp_utc":"2026-03-01T14:00:00Z","temperature_2m_c":22.0,"relative_humidity_2m_pct":75.0,"wind_speed_10m_ms":1.25}
```

**En este proyecto (Python escribe).**

<!-- fragmento: python/src/clima_medellin/jsonlines.py -->
```python
        for ts, row in zip(frame.index, frame[columns].itertuples(index=False), strict=True):
            record = {
                "location_code": location_code,
                "source": source,
                "timestamp_utc": _format_timestamp(ts),
            }
            for column, value in zip(columns, row, strict=True):
                record[column] = None if value is None or math.isnan(value) else float(value)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
```

- `_format_timestamp` produce `2026-03-01T13:00:00Z`: UTC con sufijo `Z`, el formato que Java acepta con `Instant.parse`.
- `math.isnan(value)` detecta los `NaN` de Pandas y los escribe como `None`, que `json.dumps` convierte en `null`.

**En este proyecto (Java valida antes de escribir).** `JsonLines.read` lee **todas** las líneas y comprueba cada una (JSON válido, campos conocidos, fuente y ubicación correctas, timestamp con `Z`, valores numéricos o `null`). Solo si todo el archivo es válido, `ImportCommand` abre la base:

<!-- fragmento: java/src/main/java/co/climamedellin/cli/ImportCommand.java -->
```java
        // Primero se valida el archivo entero; la base solo se abre si todo es correcto.
        List<JsonLines.Row> rows = JsonLines.read(options.path("file"), source,
                locationData.code());
        err.println("[import] " + rows.size() + " líneas válidas de " + source);

        try (Database database = Database.open(options.db())) {
```

**Cuidado.** Validar línea a línea mientras se inserta dejaría la base a medias si la línea 5 000 estuviera rota; validar primero garantiza «todo o nada» a nivel de archivo.

### 4.4 El camino completo de ObjectDB a Python

**Concepto.** Para analizar, Python necesita los datos de la base como DataFrame. Pide a Java una **exportación** de un rango: Java consulta ObjectDB con JPQL (sección 2.6), escribe un JSON Lines en `exchange/` y responde con la ruta; Python lo lee con Pandas.

**Sintaxis básica.**

```python
bridge = JavaBridge()                                  # base en data/clima.odb
tabla = bridge.export("ERA5", inicio_utc, fin_utc)     # DataFrame indexado por timestamp_utc
```

**En este proyecto (Java escribe una línea por registro).**

<!-- fragmento: java/src/main/java/co/climamedellin/cli/ExportCommand.java -->
```java
            List<ObjectNode> lines = source == Source.ERA5
                    ? store.findWeather(code, from, to).stream().map(JsonLines::line).toList()
                    : store.findAirQuality(code, from, to).stream().map(JsonLines::line).toList();
            int written = JsonLines.write(out, lines);
```

**En este proyecto (Python lo lee como DataFrame).**

<!-- fragmento: python/src/clima_medellin/jsonlines.py -->
```python
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    extra = ["batch_id"] if records and "batch_id" in records[0] else []
    index = pd.DatetimeIndex(
        pd.to_datetime([r["timestamp_utc"] for r in records], utc=True), name="timestamp_utc"
    )
    data = {c: [r.get(c) for r in records] for c in columns + extra}
    frame = pd.DataFrame(data, index=index)
    frame[columns] = frame[columns].astype(float)
```

- Cada línea exportada lleva también `batch_id`, el lote que insertó el registro (procedencia).
- `astype(float)` convierte los `None` en `NaN`.
- La prueba `test_round_trip_is_identical` importa una semana real de ERA5 (con un viento a `null`), la exporta y comprueba con `assert_frame_equal` que vuelve **idéntica**: mismos timestamps, mismos valores (sin errores de redondeo) y el mismo nulo.

**Ciclo de vida de los archivos.**

| Carpeta | Quién escribe | Nombre | Qué pasa después |
|---|---|---|---|
| `staging/` | Python | `<fuente>-<AAAAmmddTHHMMSSffffff>.jsonl` (único por lote) | Se borra si la importación termina con código 0; si falla se conserva y su ruta aparece en el error |
| `exchange/` | Java | `export-<fuente>.jsonl`, `coverage-<fuente>.jsonl` (nombre fijo) | Se sobrescribe en cada llamada; nunca se borra automáticamente |

**Cuidado.** Un lote fallido en `staging/` es una pista, no basura: abrirlo con un editor muestra la línea exacta que Java rechazó.

---

## 5. Ventana móvil, cobertura e intervalos faltantes

El código está en `python/src/clima_medellin/coverage.py` (funciones puras: no usan red ni base) y `update.py` (el flujo de actualización). Las reglas de diseño están en [cobertura-y-franjas.md](cobertura-y-franjas.md). Las pruebas son `test_coverage.py` (unitarias) y `test_update.py` (JAR real, base temporal y una API falsa que sirve valores de las muestras).

### 5.1 La ventana móvil y el 29 de febrero

**Concepto.** El proyecto analiza siempre **el último año**: de las 00:00 locales del mismo día del año anterior a las 00:00 locales de hoy (D-016). La fecha de referencia es la de Medellín, no la UTC, y los extremos se convierten a UTC para compararlos con los datos guardados. Si hoy es 29 de febrero, «el mismo día del año anterior» no existe y se usa el 28 (DP-09).

**Sintaxis básica.**

```python
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

hoy = date(2026, 10, 18)
inicio = hoy.replace(year=hoy.year - 1)                       # 2025-10-18
medianoche = datetime.combine(inicio, time.min, tzinfo=ZoneInfo("America/Bogota"))
medianoche.astimezone(ZoneInfo("UTC"))                        # 2025-10-18 05:00:00+00:00
date(2028, 2, 29).replace(year=2027)                          # ValueError: day is out of range
```

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/coverage.py -->
```python
def one_year_before(day: date) -> date:
    """Mismo día del año anterior; el 29 de febrero pasa al 28 de febrero (DP-09)."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def _local_midnight_utc(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=LOCAL_TZ).astimezone(UTC)


def window(today: date) -> Window:
    """Ventana [mismo día del año anterior, hoy) a las 00:00 locales, con extremos en UTC."""
    start = one_year_before(today)
    return Window(start, today, _local_midnight_utc(start), _local_midnight_utc(today))
```

- `day.replace(year=...)` lanza `ValueError` solo con el 29 de febrero; el `except` lo sustituye por el 28.
- `_local_midnight_utc` crea las 00:00 en America/Bogota y las pasa a UTC (las 05:00 UTC).
- La ventana no siempre tiene 365 días: con D = 2028-03-01 tiene 366 porque incluye el 29-02-2028. Por eso los pasos esperados se calculan siempre a partir de la ventana real, nunca se fijan en 8 760.

| D (hoy) | Inicio | Días | Probado en |
|---|---|---|---|
| 2026-10-09 | 2025-10-09 | 365 | `test_window_days` |
| 2028-02-29 | 2027-02-28 | 366 | `test_window_days` |
| 2028-03-01 | 2027-03-01 | 366 | `test_window_days` |
| 2029-03-01 | 2028-03-01 | 365 | `test_window_days` |

**Cuidado.** Usar `date.today()` (la fecha del sistema, que puede estar en UTC) en lugar de la fecha de Medellín haría que, a partir de las 19:00 locales, la ventana avanzara un día antes de tiempo. `coverage.today_local()` usa siempre America/Bogota.

### 5.2 El fin efectivo de cada fuente

**Concepto.** No tiene sentido esperar datos que la fuente aún no publica. El **fin efectivo** es el primer instante que ya no se espera ni se guarda: para ERA5, las 00:00 UTC de D−4 (el día D−5 llega completo, PV-04); para CAMS, el fin de la ventana.

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/coverage.py -->
```python
def effective_end(source: str, win: Window, today: date) -> datetime:
    """Primer instante UTC que ya no se espera ni se guarda para la fuente (exclusivo)."""
    if source == "ERA5":
        first_unpublished_day = today - timedelta(days=ERA5_LAST_FULL_DAY_OFFSET - 1)
        published_until = datetime.combine(first_unpublished_day, time.min, tzinfo=UTC)
        return min(win.end_utc, published_until)
    return win.end_utc
```

Con D = 2026-10-18: ERA5 termina en `2026-10-14T00:00Z` y CAMS en `2026-10-18T05:00Z`. La normalización (sección 3.4) elimina cualquier valor en o después de ese instante.

### 5.3 Esperados frente a existentes: los faltantes

**Concepto.** Se comparan dos **conjuntos**: las horas que deberían existir (todas las horas en punto de `[inicio, fin efectivo)`) y las que existen en la base. Su **diferencia** son los faltantes. Pandas trabaja con índices de fechas como si fueran conjuntos.

**Sintaxis básica.**

```python
import pandas as pd

esperados = pd.date_range("2026-03-01 00:00", "2026-03-01 05:00", freq="h", tz="UTC")
existentes = esperados.delete([2, 3])                 # faltan las 02:00 y las 03:00
esperados.difference(existentes)                      # DatetimeIndex(['2026-03-01 02:00', '2026-03-01 03:00'])
```

**En este proyecto.** `expected_steps(inicio, fin)` construye el índice horario con `pd.date_range(..., freq="h", inclusive="left")` (el extremo final queda fuera) y `missing_steps(esperados, existentes)` devuelve `esperados.difference(existentes)`. Los existentes son los timestamps que devuelve el subcomando `coverage` del JAR (sección 4). Como nunca se guardan filas sin ningún dato (DP-12), «existe un registro» significa «hay al menos un valor real».

### 5.4 Agrupar faltantes en intervalos y en peticiones por fecha

**Concepto.** Pedir hora a hora sería absurdo: las horas consecutivas se agrupan en **intervalos**, y como la API recibe **fechas** (días completos), cada intervalo se convierte en un rango de fechas UTC. Los rangos que, ya en días, se tocan o se solapan se fusionan en una sola petición.

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/coverage.py -->
```python
    intervals: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for ts in steps.sort_values():
        if intervals and ts - intervals[-1][1] == STEP:
            intervals[-1] = (intervals[-1][0], ts)
        else:
            intervals.append((ts, ts))
    return intervals
```

- Se recorren los faltantes en orden. Si la hora actual está justo una hora (`STEP`) después del final del intervalo abierto, lo amplía; si no, abre uno nuevo.

<!-- fragmento: python/src/clima_medellin/coverage.py -->
```python
    requests: list[tuple[date, date]] = []
    for first, last in intervals:
        start, end = first.date(), last.date()
        if requests and start <= requests[-1][1] + timedelta(days=1):
            requests[-1] = (requests[-1][0], max(requests[-1][1], end))
        else:
            requests.append((start, end))
    return requests
```

- Cada intervalo pasa a `(fecha de su primera hora, fecha de su última hora)`.
- Si el nuevo rango empieza como mucho un día después del final del anterior, se fusionan (dos peticiones de días contiguos serían una sola).

Ejemplo de la documentación (prueba `test_documentation_example_yields_two_one_day_requests`): faltan las horas del 3 de marzo de 13:00 a 18:00 UTC y todo el 10 de marzo → dos intervalos → dos peticiones de un día (3 y 10 de marzo). Las horas del 3 de marzo que ya existían vuelven a llegar, pero la clave natural las detecta como duplicadas y no se tocan (sección 2.5).

**Cuidado.** La primera petición de una carga inicial empieza a las 00:00 UTC del primer día, cinco horas antes de la ventana (que empieza a las 05:00 UTC). `update.execute_plan` descarta esas horas antes de importar:

<!-- fragmento: python/src/clima_medellin/update.py -->
```python
        normalized = normalize(request.source, payload, end)
        # La petición pide días UTC completos: el primero empieza antes de la ventana.
        before = normalized.frame.index < pd.Timestamp(plan.window.start_utc)
        frame = normalized.frame[~before]
```

### 5.5 Métricas por variable y estado

**Concepto.** La cobertura se mide **por variable** (un registro puede tener la temperatura y no el viento): pasos válidos (con valor) sobre esperados, más el **hueco máximo** (tramo consecutivo de faltantes más largo) y el número de huecos. El estado combina dos criterios (D-014): porcentaje ≥ 98 % **y** hueco máximo ≤ 6 h.

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/coverage.py -->
```python
    valid_in_window = expected.intersection(valid)
    gaps = group_intervals(missing_steps(expected, valid_in_window))
    longest = max((int((last - first) / STEP) + 1 for first, last in gaps), default=0)
    percent = 100.0 * len(valid_in_window) / len(expected) if len(expected) else 0.0
```

<!-- fragmento: python/src/clima_medellin/coverage.py -->
```python
    if records_in_window == 0:
        return "SIN_DATOS"
    if all(v.percent >= MIN_COVERAGE_PCT and v.max_gap_hours <= MAX_GAP_HOURS for v in variables):
        return "COMPLETA"
    return "PARCIAL"
```

- `expected.intersection(valid)` cuenta solo los valores dentro de la ventana; lo que haya fuera no suma.
- Los huecos se calculan con la misma función de agrupación de 5.4; la duración de un hueco es `(última − primera) / 1 h + 1` horas.
- `all(...)` exige que **todas** las variables de la fuente cumplan los dos umbrales.

| Caso (ventana de 8 760 h) | Cobertura | Hueco máximo | Estado |
|---|---|---|---|
| Faltan 6 horas seguidas | 99,93 % | 6 h | COMPLETA |
| Faltan 7 horas seguidas | 99,92 % | 7 h | PARCIAL |
| Falta 1 hora de cada 34 | ≈ 97 % | 1 h | PARCIAL |
| Ningún registro en la ventana | 0 % | — | SIN_DATOS |

Con la API falsa de las pruebas (valores de las muestras) y D = 2026-10-18, una carga inicial deja ERA5 con 8 659 horas esperadas y válidas y CAMS con 8 760: las dos fuentes quedan `COMPLETA`, y una segunda actualización inmediata no planifica ninguna petición.

**Cuidado.** Un 99 % con un único hueco de 80 horas pasaría por porcentaje, pero dejaría más de 3 días sin datos: por eso el estado exige también el hueco máximo.

### 5.6 El flujo de actualización

**Concepto.** `update.py` encadena las piezas: **cobertura → plan → descarga → normalización → recorte → importación → nueva cobertura**. El plan y la ejecución están separados para que la CLI pueda mostrar el plan y pedir confirmación antes de descargar.

**Sintaxis básica.**

```python
from clima_medellin.bridge import JavaBridge
from clima_medellin.coverage import today_local
from clima_medellin.update import execute_plan, plan_update

bridge = JavaBridge()
plan = plan_update(bridge, today_local())          # [PlannedRequest("ERA5", 2026-03-10, 2026-03-10), ...]
resultados = execute_plan(bridge, plan)            # descarga e importa cada petición
```

- Si la API no devuelve ningún valor para una petición, se importa igualmente un lote vacío: queda un `IngestionBatch` con 0 recibidos y 0 insertados, que demuestra que el hueco es de la fuente y no un fallo del proceso (prueba `test_empty_api_answer_still_records_a_batch`).
- La función `fetch` se inyecta: en producción es `openmeteo.fetch`; en las pruebas, `FakeOpenMeteo` (`python/tests/fakes.py`).

---

## 6. Zonas horarias, franjas y estadística descriptiva

El código está en `python/src/clima_medellin/`: `split.py` (entrenamiento y prueba), `dataset.py` (tabla de análisis), `bands.py` (franjas y perfil diurno) y `descriptive.py` (estadísticas). Las reglas están en [cobertura-y-franjas.md](cobertura-y-franjas.md#franjas-horarias). Las pruebas `test_bands.py` y `test_descriptive.py` comprueban los resultados con un día y una serie calculados a mano.

### 6.1 La tabla de análisis: unir las dos fuentes

**Concepto.** Para describir los datos se necesita una sola tabla con las cuatro variables. ERA5 y CAMS se exportan por separado (sección 4.4) y se **unen por el índice** (el timestamp UTC). Un `outer join` conserva las horas que solo tiene una de las dos fuentes; por ejemplo, los últimos días de PM2.5, para los que ERA5 aún no ha publicado.

**Sintaxis básica.**

```python
meteo = pd.DataFrame({"t": [20.0]}, index=[h10])
aire = pd.DataFrame({"pm": [12.0, 15.0]}, index=[h10, h11])
meteo.join(aire, how="outer")
#        t     pm
# h10  20.0  12.0
# h11   NaN  15.0
```

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/dataset.py -->
```python
    joined = weather[ERA5.columns].join(air[CAMS_GLOBAL.columns], how="outer")
    return joined.sort_index()[COLUMNS]
```

- Se seleccionan solo las columnas canónicas (se descarta `batch_id`).
- La regresión (sección 7) usará en cambio un `inner join` y quitará las filas con algún nulo, porque necesita las cuatro variables a la vez.

### 6.2 De UTC a hora de Medellín

**Concepto.** Los datos se guardan en UTC (D-008), pero las franjas son locales. Un índice de Pandas **con zona horaria** se convierte con `tz_convert`, que cambia la hora mostrada sin cambiar el instante. Se usa el nombre de la zona (`America/Bogota`) y no un desfase fijo de −5, aunque Colombia no tenga horario de verano (PV-16).

**Sintaxis básica.**

```python
idx = pd.DatetimeIndex(["2026-04-13 00:00"], tz="UTC")
idx.tz_convert("America/Bogota")      # 2026-04-12 19:00:00-05:00  (¡el día anterior!)
```

**Cuidado.** `tz_localize` y `tz_convert` no son lo mismo: `tz_localize` **declara** la zona de unas horas sin zona; `tz_convert` **traduce** unas horas que ya tienen zona. Aplicar `tz_localize("America/Bogota")` a horas UTC las desplazaría 5 horas.

### 6.3 Franjas: `groupby` por día civil local y mínimo de 2 horas

**Concepto.** Cada franja (mañana 07–09, tarde 13–15, noche 19–21) vale el **promedio de los valores no nulos** de sus 3 horas, y **NaN si hay menos de 2** (D-009). El promedio se agrupa por el **día civil local**: la franja de la noche del 12 de abril son las 00:00–02:00 UTC del **13**, y agrupar por día UTC la asignaría al día equivocado.

**Sintaxis básica.**

```python
s = pd.Series([17.8, None, 19.6], index=horas_locales_7_8_9)
s.mean()     # 18.7  (mean ignora los NaN)
s.count()    # 2     (count cuenta solo los valores no nulos)
```

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/bands.py -->
```python
    local = to_local(frame)
    pieces = {}
    for band, hours in BANDS.items():
        in_band = local[local.index.hour.isin(hours)]
        # Se agrupa por el día civil local, no por el día UTC: la noche (19-21 h) cae
        # en el día UTC siguiente (00-02 UTC).
        grouped = in_band.groupby(in_band.index.date)
        mean, count = grouped.mean(), grouped.count()
        pieces[band] = mean.where(count >= MIN_VALID_HOURS)
```

- `local.index.hour.isin(hours)` se queda con las filas cuya hora **local** es 7, 8 o 9 (o 13–15, o 19–21).
- `groupby(in_band.index.date)` agrupa por la fecha local de cada fila.
- `mean()` promedia ignorando los NaN y `count()` cuenta los valores no nulos de cada grupo.
- `mean.where(count >= 2)` deja el promedio donde hay al menos 2 valores y pone NaN donde no. **No se interpola**: un NaN significa «ese día no hay datos suficientes para esa franja».
- Una hora **sin fila** cuenta igual que una hora con NaN: no entra en `count`.

El resultado es una tabla con un día local por fila y columnas `(variable, franja)`. Comprobación a mano (prueba `test_hand_computed_day`): el 12 de abril, temperatura 17,8 °C a las 07:00, falta a las 08:00 y 19,6 °C a las 09:00 → mañana = (17,8 + 19,6) / 2 = **18,7 °C**; si en la tarde solo hay un valor → **NaN**.

**Cuidado.** Para PM2.5, las franjas de la mañana y de la noche empiezan en un empalme del pronóstico de CAMS (12 y 00 UTC); ver [cobertura-y-franjas.md](cobertura-y-franjas.md#pm25-horario-y-empalmes-del-pronóstico).

### 6.4 Perfil diurno solo con el entrenamiento

**Concepto.** El **perfil diurno** es la media de cada variable para cada hora local (0–23): muestra el ciclo típico del día y si las franjas caen en sus momentos característicos. Se calcula **solo con el periodo de entrenamiento** (D-018): si se usara todo el año y después se decidiera algo a partir de él, el periodo de prueba influiría en el diseño (fuga de información, [regresion.md](regresion.md#pipeline-y-prevención-de-fuga-de-información)).

**En este proyecto.** La separación vive en `split.py`: entrenamiento = 9 meses naturales desde el inicio de la ventana, 24 h descartadas y prueba = el resto (con la ventana de 2025-10-18 a 2026-10-18, el entrenamiento termina el 2026-07-18 y la prueba empieza el 2026-07-19, ambos a las 00:00 locales).

<!-- fragmento: python/src/clima_medellin/bands.py -->
```python
    local = to_local(split.train(frame))
    grouped = local.groupby(local.index.hour)
    profile = pd.concat({"media": grouped.mean(), "n": grouped.count()}, axis=1).swaplevel(axis=1)
    columns = pd.MultiIndex.from_product([frame.columns, ["media", "n"]])
    profile = profile.reindex(index=range(24), columns=columns)
```

- `split.train(frame)` filtra `[train_start, train_end)`; la prueba `test_diurnal_profile_uses_only_the_training_period` pone valores distintos en la prueba y comprueba que no aparecen en el perfil.
- `groupby(local.index.hour)` agrupa por hora local; junto a la media se guarda `n`, el número de valores válidos, para no confundir una media de 270 datos con una de 40.
- `reindex(index=range(24))` garantiza las 24 horas aunque alguna no tenga datos.

### 6.5 Estadísticas descriptivas y percentiles

**Concepto.** Para cada variable se calculan n (valores válidos), nulos, media, mediana, desviación estándar, mínimo, máximo y los **percentiles** 5, 25, 75 y 95. Un percentil *p* es el valor por debajo del cual queda el *p* % de los datos; mediana y percentiles son **robustos**: no los mueve un pico aislado, a diferencia de la media. Son útiles para PM2.5, que es asimétrica (mediana 10,6 µg/m³ frente a media 12,9 µg/m³ en la muestra anual).

**Sintaxis básica.**

```python
s = pd.Series(range(1, 101))
s.quantile(0.25)   # 25.75 (interpolación lineal entre el 25 y el 26)
s.median()         # 50.5
```

**En este proyecto.**

<!-- fragmento: python/src/clima_medellin/descriptive.py -->
```python
        values = frame[column]
        valid = values.dropna()
        row = {
            "n": int(valid.size),
            "nulos": int(values.isna().sum()),
            "media": valid.mean(),
            "mediana": valid.median(),
            "desv": valid.std(),
            "min": valid.min(),
            "max": valid.max(),
        }
        for name, q in PERCENTILES.items():
            row[name] = valid.quantile(q)
```

- Todas las medidas se calculan sobre `valid` (sin NaN), y los nulos se cuentan aparte para que se vean.
- `std()` usa por defecto la desviación **muestral** (divide entre n − 1).
- `describe_bands` hace lo mismo por franja: la media de las franjas válidas y el número de **días válidos**, para saber en cuántos días se apoya cada media.

**Cuidado.** `nulos` cuenta los valores nulos de las filas presentes; las horas que no tienen ningún registro no aparecen aquí: las informa la cobertura (sección 5).
