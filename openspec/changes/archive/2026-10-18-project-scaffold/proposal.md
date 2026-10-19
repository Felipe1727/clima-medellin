# Proposal

## Why

El repositorio solo contiene documentación de diseño: no hay proyecto Java ni Python, ni comandos de prueba, ni integración continua. Todas las especificaciones siguientes del roadmap necesitan una base común que compile, se pruebe y se valide automáticamente antes de fusionar, además del documento técnico `docs/implementacion.md` que irá creciendo con cada especificación.

## What Changes

- Nuevo proyecto Maven en `java/` (Java 25, ObjectDB 2.9.5 `objectdb-jk`, Jackson, JUnit 5, maven-shade) que genera `java/target/clima-medellin.jar`. El JAR tiene un punto de entrada que, sin subcomando o con uno desconocido, imprime un único objeto JSON de error por stdout y termina con código 1.
- Nuevo proyecto Python en `python/` gestionado con uv (Python 3.14): paquete `clima_medellin` con el comando `clima-medellin`, dependencias del proyecto, pytest y ruff configurados y una prueba de humo.
- Flujo de GitHub Actions `.github/workflows/ci.yml` que instala, prueba y analiza el código en cada pull request y en cada push a `main`.
- Nuevo documento `docs/implementacion.md` (propósito, índice, convención de fragmentos, cómo compilar y ejecutar) con al menos un fragmento real de código.
- Prueba de pytest que verifica que cada fragmento marcado en `docs/implementacion.md` sigue apareciendo literalmente en su archivo de origen.
- README actualizado (árbol de carpetas y tabla de documentación) y `.gitignore` revisado para los artefactos de compilación y ejecución.
- Comandos del proyecto escritos en el `.claude/CLAUDE.md` local (no versionado).

## Capabilities

### New Capabilities
- `jar-cli`: contrato de línea de comandos del JAR de persistencia (salida JSON única por stdout, códigos de salida); esta especificación fija el caso de uso inválido y las siguientes añadirán los subcomandos.
- `app-cli`: comando de terminal `clima-medellin` instalado por el proyecto Python.
- `implementation-guide`: documento técnico `docs/implementacion.md` y la garantía de que sus fragmentos reales coinciden con el código.

### Modified Capabilities
<!-- Ninguna: no existen especificaciones previas. -->

## Impact

- Código nuevo: `java/`, `python/`, `.github/workflows/ci.yml`, `docs/implementacion.md`.
- Dependencias nuevas: ObjectDB (repositorio `https://m2.objectdb.com`), Jackson, JUnit 5, pandas, scikit-learn, statsmodels, matplotlib, requests, pytest, ruff.
- La integración continua pasa a ser una puerta obligatoria para fusionar las especificaciones siguientes.
