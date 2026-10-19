# Design

## Context

El repositorio no tiene código. El equipo local dispone de Java 25, Maven 3.9.11, uv 0.9.28 y Python 3.14. La pila está fijada en `openspec/roadmap.md` (Guidelines). El artefacto `objectdb-jk` 2.9.5 declara `jakarta.persistence-api` 3.1.0 con ámbito `provided`, es decir, no lo trae consigo, e incluye un `module-info.class`.

## Goals / Non-Goals

**Goals:**
- Que `mvn verify`, `uv run pytest` y `uv run ruff check .` funcionen desde el primer commit, en local y en CI.
- Fijar el sobre JSON de respuesta del JAR para que los subcomandos futuros lo reutilicen.
- Dejar operativa la verificación de fragmentos de `docs/implementacion.md`.

**Non-Goals:**
- Entidades, acceso a ObjectDB o subcomandos reales (especificaciones `persistence` y `bridge`).
- El menú de la CLI (especificación `cli-integration`).

## Decisions

### Proyecto Maven único con JAR "fat"
- `groupId` `co.climamedellin`, `artifactId` `clima-medellin`, `maven.compiler.release` 25.
- Repositorio `https://m2.objectdb.com`; dependencias `com.objectdb:objectdb-jk:2.9.5`, `jakarta.persistence:jakarta.persistence-api:3.1.0` (explícita, porque ObjectDB la declara `provided` y el JAR fat debe contenerla), `com.fasterxml.jackson.core:jackson-databind` y `org.junit.jupiter:junit-jupiter` (test).
- `maven-shade-plugin` en la fase `package` con `ManifestResourceTransformer` (`co.climamedellin.cli.Main`), excluyendo `module-info.class` y las firmas `META-INF/*.SF|*.DSA|*.RSA`. `<finalName>clima-medellin</finalName>` hace que el resultado sea `java/target/clima-medellin.jar`.
- Alternativa descartada: `maven-assembly-plugin`; shade maneja mejor los descriptores duplicados.

### Sobre JSON de respuesta del JAR
- Éxito: `{"ok": true, ...campos del subcomando}`. Error: `{"ok": false, "error": {"type": "<TIPO>", "message": "<texto en español>"}}`.
- Tipos y códigos: `USAGE`→1, `DATA`→2, `DATABASE`→3, `UNEXPECTED`→4 (DP-05). En esta especificación solo se usa `USAGE`.
- `Main.main` delega en un método `run(String[] args, PrintStream out, PrintStream err)` que devuelve el código de salida; `main` llama a `System.exit`. Así las pruebas JUnit verifican stdout y el código sin lanzar un proceso.
- El JSON se serializa con Jackson en una sola línea.

### Proyecto Python con uv y diseño `src/`
- `python/pyproject.toml` con backend `hatchling`, `requires-python = ">=3.14"`, `python/.python-version` con `3.14`, `uv.lock` versionado.
- Dependencias: pandas, scikit-learn, statsmodels, matplotlib, requests. Grupo `dev`: pytest, ruff.
- Script `clima-medellin = "clima_medellin.cli:main"`. `main` usa argparse: `--version` imprime `clima-medellin <versión>`; sin opciones imprime un aviso en español de que el menú aún no está disponible.
- Ruff: `line-length = 100`, reglas `E, F, I, UP, B`. Pytest: `testpaths = ["tests"]`.

### Verificación de fragmentos
- `python/tests/test_docs_excerpts.py` localiza la raíz del repositorio desde la ruta del propio archivo, busca con una expresión regular cada `<!-- fragmento: RUTA -->` seguido de un bloque ```` ``` ````, normaliza los espacios finales de cada línea y comprueba que el texto del bloque es una subcadena del archivo citado (también normalizado).
- Falla si no hay ningún fragmento, si la ruta no existe o si el texto no aparece; el mensaje incluye la ruta.
- La lógica de extracción vive en la propia prueba (es una herramienta de verificación, no parte de la aplicación), con pruebas unitarias propias sobre textos de ejemplo para los tres casos de la especificación.

### CI
- Un único job `ubuntu-latest`: `actions/checkout@v4`, `actions/setup-java@v4` (temurin 25, caché de Maven), `astral-sh/setup-uv@v6`, y los pasos Install, Test y Lint con los comandos del roadmap.
- Se dispara en `pull_request` y en `push` a `main`.

## Risks / Trade-offs

- [`m2.objectdb.com` caído] → la compilación en CI falla; la caché de Maven de `setup-java` reduce la exposición. Si ocurre, es una condición de parada del run.
- [Ruedas de Python 3.14 no disponibles para alguna dependencia] → `uv sync` fallaría; se detecta en esta misma especificación y se resolvería ajustando versiones dentro de la pila fijada.
- [Fragmentos con espacios finales distintos] → la normalización de espacios finales evita falsos fallos; cualquier otra diferencia sí debe fallar.
