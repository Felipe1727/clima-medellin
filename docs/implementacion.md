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
| 3. Descarga de Open-Meteo y normalización con Pandas | Pendiente | `ingest` |
| 4. Puente Java↔Python: subprocesos, JSON Lines y de ObjectDB a Python | Pendiente | `bridge` |
| 5. Ventana móvil, cobertura e intervalos faltantes | Pendiente | `coverage` |
| 6. Zonas horarias, franjas y estadística descriptiva | Pendiente | `bands-stats` |
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
