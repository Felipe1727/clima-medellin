# Proposal

## Why

La base ya se llena y se mide su cobertura; falta **describir** los datos (Fase 6): las franjas de mañana, tarde y noche en hora de Medellín, el perfil diurno que permite comprobar si esas franjas capturan los momentos característicos del día y las estadísticas descriptivas que mostrará la opción 4 del menú.

## What Changes

- Separación temporal de la ventana según D-018 (entrenamiento = 9 meses naturales desde el inicio, hueco de 24 h, prueba = resto), con fechas exactas; la usarán el perfil diurno y la regresión.
- Tabla de análisis de la ventana: exportación de ERA5 y CAMS global unidas por timestamp.
- Franjas por día civil local y variable (07–09, 13–15, 19–21 h; promedio de los valores no nulos; NaN si hay menos de 2), con la franja de la noche asignada al día local correcto.
- Perfil diurno por hora local (0–23) calculado solo con el periodo de entrenamiento, con el número de valores válidos por hora.
- Estadísticas descriptivas por variable (n, nulos, media, mediana, desviación, mínimo, máximo, p5, p25, p75, p95) y por franja (media y días válidos).
- Documentación: sección 6 de `docs/implementacion.md`, `docs/cobertura-y-franjas.md` final y Fase 6 en `docs/fases.md`.

## Capabilities

### New Capabilities
- `temporal-split`: división de la ventana en entrenamiento, hueco y prueba con fechas exactas.
- `descriptive-analysis`: franjas horarias, perfil diurno y estadísticas descriptivas de las cuatro variables.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código nuevo: `python/src/clima_medellin/split.py`, `dataset.py`, `bands.py`, `descriptive.py`, con sus pruebas.
- Documentación: `docs/implementacion.md`, `docs/cobertura-y-franjas.md`, `docs/fases.md`, `docs/decisiones.md`.
