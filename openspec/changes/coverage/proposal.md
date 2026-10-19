# Proposal

## Why

Con el puente listo, la aplicación ya puede guardar y leer, pero no sabe **qué** pedir ni si lo guardado basta para analizar. La Fase 5 define la ventana móvil, mide la cobertura con los criterios de D-014 y descarga solo lo que falta respetando la latencia de cada fuente (D-015, D-016).

## What Changes

- Funciones puras de cobertura: ventana móvil a partir de la fecha D en America/Bogota (con la regla del 29 de febrero), fin efectivo por fuente (ERA5: 00:00 UTC de D−4; CAMS: fin de la ventana), pasos horarios esperados, faltantes, agrupación en intervalos consecutivos y conversión a fechas UTC de petición con fusión de días contiguos.
- Métricas por variable (esperados, válidos, porcentaje, hueco máximo, número de huecos) y estado de la fuente (`COMPLETA`, `PARCIAL`, `SIN_DATOS`) con los umbrales del 98 % y 6 h.
- Flujo de actualización: cobertura → plan de peticiones → descarga → normalización → recorte a [inicio de la ventana, fin efectivo) → lote en `staging/` → `import` → nueva cobertura. Un intervalo para el que la API no devuelve datos queda registrado como un lote con 0 insertados.
- Documentación: sección 5 de `docs/implementacion.md`; `docs/cobertura-y-franjas.md`, `docs/decisiones.md` (D-014 definitiva) y `docs/fases.md` (Fase 5).

## Capabilities

### New Capabilities
- `data-coverage`: ventana móvil, fin efectivo por fuente y medición de la cobertura con su estado.
- `incremental-update`: plan y ejecución de la descarga de solo los intervalos que faltan.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código nuevo: `python/src/clima_medellin/coverage.py` y `update.py`; pruebas unitarias y de integración (JAR real, base temporal y una capa HTTP falsa que sirve valores de las muestras).
- Documentación: `docs/implementacion.md`, `docs/cobertura-y-franjas.md`, `docs/decisiones.md`, `docs/fases.md`.
