# Tasks

## 1. Proyecto Java

- [x] 1.1 Crear `java/pom.xml` (Java 25, repositorio de ObjectDB, `objectdb-jk` 2.9.5, `jakarta.persistence-api` 3.1.0, Jackson, JUnit 5, surefire, shade con `finalName` `clima-medellin`) y verificar que `mvn -q -DskipTests package` produce `java/target/clima-medellin.jar`
- [x] 1.2 Implementar `co.climamedellin.cli.Main` con `run(args, out, err)` y el sobre JSON de error `USAGE` (código 1), con comentarios en español, y verificar con `java -jar java/target/clima-medellin.jar foo` que stdout es un único JSON y el código es 1
- [x] 1.3 Escribir pruebas JUnit para la ejecución sin argumentos y con subcomando desconocido (JSON válido de una línea, `ok=false`, `type=USAGE`, mensaje que menciona el subcomando, código 1) y verificar que `mvn -q verify` pasa

## 2. Proyecto Python

- [x] 2.1 Crear `python/pyproject.toml`, `python/.python-version` y el paquete `python/src/clima_medellin/` con dependencias, grupo `dev`, configuración de ruff y pytest; verificar que `uv sync` termina sin errores y genera `uv.lock`
- [x] 2.2 Implementar `clima_medellin.cli:main` (`--version` y aviso sin opciones) y verificar que `uv run clima-medellin --version` imprime la versión
- [x] 2.3 Escribir la prueba de humo del comando (versión y aviso, código 0) y verificar que `uv run pytest` y `uv run ruff check .` pasan

## 3. Guía técnica y verificación de fragmentos

- [x] 3.1 Crear `docs/implementacion.md` en español (propósito, índice con las secciones previstas por especificación, convención de fragmentos, compilar y ejecutar) con una primera sección sobre el punto de entrada del JAR que incluya un fragmento real de `Main.java` en el formato Concepto / Sintaxis básica / En este proyecto / Cuidado
- [x] 3.2 Implementar `python/tests/test_docs_excerpts.py` (extracción de fragmentos, comparación normalizada, fallo sin fragmentos, ruta inexistente o texto distinto) con pruebas sobre textos de ejemplo de los tres casos, y verificar que `uv run pytest` pasa con la guía real

## 4. Integración continua, README y configuración

- [ ] 4.1 Crear `.github/workflows/ci.yml` (checkout, Java 25 temurin con caché de Maven, setup-uv, Install, Test, Lint) y verificar la sintaxis ejecutando localmente los tres comandos del roadmap
- [ ] 4.2 Actualizar `README.md` (árbol de carpetas real y `implementacion.md` en la tabla de documentación) y revisar `.gitignore`; verificar con `git status` tras compilar y probar que no aparecen artefactos generados
- [ ] 4.3 Escribir los comandos del proyecto en el `.claude/CLAUDE.md` local y marcar el avance correspondiente en `docs/fases.md`; verificar que `git status` no muestra `.claude/CLAUDE.md`
- [ ] 4.4 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `project-scaffold` como hecho en `openspec/roadmap.md`.
