# Design

## Context

Existen `RecordStore` (Java) y `normalize` (Python). Hallazgos previos relevantes:
- Un segundo proceso que abre el mismo `.odb` falla de inmediato con `PersistenceException` («currently in use by another process») (PV-15).
- Con Java 25, ObjectDB imprime en stderr un aviso sobre `sun.misc.Unsafe`; se silencia lanzando la JVM con `--sun-misc-unsafe-memory-access=allow`.

## Goals / Non-Goals

**Goals:**
- Contrato estable y probado de extremo a extremo: DataFrame → staging → import → export → DataFrame idéntico.
- Errores clasificados en Java y traducidos en Python.

**Non-Goals:**
- Cálculo de cobertura, ventana e intervalos (especificación `coverage`): aquí `coverage` solo devuelve lo guardado.
- Menú y mensajes de la CLI (especificación `cli-integration`).

## Decisions

### Opciones del JAR
- Sintaxis `subcomando --opción valor ...`; un parser pequeño (`Options`) convierte los pares en un mapa y valida opciones conocidas por subcomando. Errores → `UsageException` (código 1).
- `import --file F --meta M [--db D]`. `--meta` es un JSON en una sola cadena: `{"source", "location": {"code","name","latitude","longitude","elevation_m","timezone"}, "requested_start_utc", "requested_end_utc", "endpoint", "params": {...}, "notes"}`. Alternativa descartada: una opción por campo (12 opciones): más larga y más frágil; Python pasa la lista de argumentos sin shell, así que no hay problemas de comillas.
- `coverage --location C --source S --out F [--db D]` y `export --location C --source S --from T --to T --out F [--db D]`.
- `--db` por defecto `data/clima.odb` (relativo al directorio de trabajo); Python siempre lo pasa explícito.

### Validación antes de escribir
- `import` lee y valida todas las líneas (JSON válido, objeto, `source` y `location_code` iguales a los metadatos, `timestamp_utc` ISO con `Z`, variables numéricas o `null`, sin campos desconocidos) y solo entonces abre la base. Un error → `DataException` con el número de línea (código 2) y la base queda intacta.
- Las filas sin ningún valor se pasan igualmente a `RecordStore`, que las rechaza y las cuenta.

### Clasificación de errores en `Main`
- `UsageException` → 1, `DataException` (incluye archivo inexistente o ilegible) → 2, `PersistenceException` → 3, cualquier otra `RuntimeException` → 4. El mensaje de Java va en español; la traza solo a stderr.

### Python
- `paths.py`: raíz del repositorio (`Path(__file__).parents[3]`), `data/clima.odb`, `staging/`, `exchange/`, `outputs/` y el JAR `java/target/clima-medellin.jar`.
- `jsonlines.py`: `write_frame(frame, source, location_code, path)` (NaN → `null`, timestamps con `Z`) y `read_frame(path, source)` (índice UTC con zona, columnas canónicas en orden, `batch_id` si existe).
- `bridge.py`: `JavaBridge(db_path, *, jar, staging_dir, exchange_dir, verbose, java)` con `import_frame(source, frame, meta)`, `coverage(source)` y `export(source, start, end)`. `_run` usa `subprocess.run([...], capture_output=True, text=True, encoding="utf-8")`, interpreta stdout con `json.loads` exigiendo una sola línea y lanza `BridgeError(code, error_type, message, staging_file)` con el texto en español del código.
- Nombre del archivo de staging: `<fuente>-<AAAAmmddTHHMMSSffffff>.jsonl` (UTC) para que dos lotes nunca colisionen. Exportaciones: `exchange/export-<fuente>.jsonl`; cobertura: `exchange/coverage-<fuente>.jsonl`.
- `coverage(source)` devuelve un `CoverageSnapshot(summary, existing)` donde `existing` es un DataFrame indexado por timestamp con una columna booleana por variable.

### Pruebas
- Java: JUnit sobre `Main.run` con archivos y bases en `@TempDir` (import, repetición, línea corrupta en cada variante, archivo inexistente, opción desconocida, fuente inválida, coverage, export, `--db` que es un directorio).
- Python: pruebas con el JAR real (lo construye el comando Test antes de pytest) contra una base temporal: ida y vuelta, repetición, línea corrupta con mensaje en español y archivo de staging conservado, subcomando desconocido, coverage, modo detallado. Si el JAR no existe, las pruebas fallan con un mensaje que indica cómo construirlo.

## Risks / Trade-offs

- [Arranque de la JVM por llamada] → del orden de 0,5–1 s; aceptable para una CLI académica (D-001).
- [Precisión de los decimales] → Python escribe el `repr` más corto de cada `float` y Jackson también; la prueba de ida y vuelta lo comprueba con igualdad exacta.
