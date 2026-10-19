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
| 2. ObjectDB: entidades, transacciones, inserción y consultas JPQL | Pendiente | `persistence` |
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
