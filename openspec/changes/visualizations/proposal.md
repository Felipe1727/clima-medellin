# Proposal

## Why

La opción 6 del menú debe producir las gráficas de [cli-y-visualizaciones.md](../../../docs/cli-y-visualizaciones.md#gráficas-previstas) (Fase 8), más el diagnóstico de los empalmes de CAMS acordado en la exploración. Cada gráfica responde una pregunta concreta y debe poder mostrarse en una ventana o guardarse como PNG, también en equipos sin pantalla gráfica.

## What Changes

- Módulo de gráficas con Matplotlib y un estilo común (paleta validada, rejilla y ejes recesivos, título, ejes con unidades, periodo y atribución «Datos: Open-Meteo.com (ERA5, CAMS)» en cada figura):
  - series temporales por variable, con los huecos como cortes de la línea;
  - perfil diurno del entrenamiento con banda de dispersión y franjas sombreadas;
  - diagramas de caja por franja con los días válidos;
  - dispersión de PM2.5 frente a cada predictora (entrenamiento);
  - matriz de correlación de las cuatro variables (entrenamiento);
  - real frente a predicho (dispersión con y = x y serie temporal superpuesta);
  - residuos (frente a predichos, en el tiempo e histograma);
  - mapa de cobertura días × horas locales por fuente (presente, parcial, ausente);
  - diagnóstico de empalmes de PM2.5 (salto medio por hora UTC).
- Salida: ventana o PNG en `outputs/<gráfica>_<AAAAmmdd-HHMMSS>.png`; si no hay pantalla disponible, PNG automático con aviso.
- Documentación: sección 8 de `docs/implementacion.md`, `docs/cli-y-visualizaciones.md` (lista definitiva, PV-18), Fase 8 en `docs/fases.md`.

## Capabilities

### New Capabilities
- `charts`: generación de las gráficas de análisis con su anotación obligatoria y su salida en ventana o PNG.

### Modified Capabilities
<!-- Ninguna. -->

## Impact

- Código nuevo: `python/src/clima_medellin/plots.py` y sus pruebas (backend Agg).
- Documentación: `docs/implementacion.md`, `docs/cli-y-visualizaciones.md`, `docs/fases.md`, `docs/decisiones.md`.
