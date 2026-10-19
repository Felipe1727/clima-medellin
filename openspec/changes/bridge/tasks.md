# Tasks

## 1. Subcomandos del JAR

- [x] 1.1 Implementar `Options`, `UsageException`, `DataException`, la lectura y escritura de JSON Lines y la clasificación de errores en `Main` (códigos 1–4), con pruebas de opción desconocida, opción sin valor, fuente inválida y `--db` que es un directorio; verificar con `mvn -q verify`
- [x] 1.2 Implementar `import` (validación completa antes de escribir, ubicación, lote con procedencia) con pruebas de importación correcta, repetida, archivo inexistente y líneas corruptas (JSON inválido, timestamp, valor no numérico, fuente distinta) sin cambios en la base; verificar con `mvn -q verify`
- [x] 1.3 Implementar `coverage` y `export` con pruebas de resumen, líneas `non_null`, base vacía, rango [from, to) ordenado y `batch_id`; verificar con `mvn -q verify`

## 2. Puente en Python

- [x] 2.1 Implementar `paths.py` y `jsonlines.py` (DataFrame ↔ JSON Lines) con pruebas de NaN → `null`, sufijo `Z` y lectura con índice UTC; verificar con `uv run pytest`
- [x] 2.2 Implementar `bridge.py` (`JavaBridge`, `BridgeError`, mensajes en español, staging y exchange, modo detallado) con pruebas contra el JAR real: ida y vuelta idéntica, repetición con 0 insertados, línea corrupta con mensaje y staging conservado, subcomando desconocido con código 1, cobertura y stderr en modo detallado; verificar con `uv run pytest`

## 3. Documentación

- [x] 3.1 Escribir la sección 4 de `docs/implementacion.md` (subprocess, JSON Lines, contrato stdout/stderr, códigos de salida, camino completo ObjectDB → Python) con fragmentos reales; verificar con `uv run pytest`
- [x] 3.2 Resolver DP-05, PV-15 y PV-19 en `docs/arquitectura.md` (argumentos definitivos, formato de cobertura, ciclo de vida de archivos), marcar la Fase 4 en `docs/fases.md` y actualizar D-003/D-004 en `docs/decisiones.md`; verificar que no quedan `[Por verificar, Fase 4]`
- [ ] 3.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `bridge` como hecho en `openspec/roadmap.md`.
