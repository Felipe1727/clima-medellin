# Tasks

## 1. Funciones de cobertura

- [x] 1.1 Implementar en `clima_medellin/coverage.py` la ventana, el fin efectivo, los pasos esperados y faltantes, la agrupación en intervalos y la conversión a fechas con fusión, con pruebas de la tabla de ventanas (365/366/366/365 días), extremos UTC, fin efectivo, ejemplo de la documentación (dos peticiones de un día) y días contiguos; verificar con `uv run pytest`
- [x] 1.2 Implementar las métricas por variable y el estado (`COMPLETA`, `PARCIAL`, `SIN_DATOS`) con pruebas de hueco de 6 h (99,93 %, COMPLETA), hueco de 7 h (PARCIAL), 97 % en huecos cortos (PARCIAL) y sin registros (SIN_DATOS); verificar con `uv run pytest`

## 2. Actualización incremental

- [ ] 2.1 Implementar `clima_medellin/update.py` (plan, ejecución con recorte a la ventana, actualización completa) y la capa HTTP falsa de pruebas; con el JAR real y una base temporal probar: carga inicial COMPLETA en ambas fuentes, segunda actualización sin peticiones, un día ausente que produce una sola petición, nada guardado en o después del fin efectivo e intento vacío con lote de 0 insertados; verificar con `uv run pytest`

## 3. Documentación

- [ ] 3.1 Escribir la sección 5 de `docs/implementacion.md` (conjuntos esperados frente a existentes, agrupación de intervalos, ventana y 29 de febrero, métricas y estado) con fragmentos reales; verificar con `uv run pytest`
- [ ] 3.2 Actualizar `docs/cobertura-y-franjas.md` (reglas implementadas, recorte al inicio de la ventana), `docs/decisiones.md` (D-014 definitiva, D-015, D-016) y `docs/fases.md` (Fase 5 completada); verificar que no quedan decisiones de la Fase 5 pendientes
- [ ] 3.3 Verificar que el workflow de CI queda en verde en el pull request de esta especificación

## Workflow follow-up

- Fusionar el pull request con squash cuando CI esté en verde.
- Archivar el cambio con OpenSpec y marcar `coverage` como hecho en `openspec/roadmap.md`.
