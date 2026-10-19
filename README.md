# Clima Medellín

Proyecto universitario para la asignatura de **Bases de Datos**. Es una aplicación de línea de comandos (CLI) que obtiene datos meteorológicos y de calidad del aire de Medellín, los limpia con Python y Pandas, los guarda en **ObjectDB** mediante Java (JPA) y los analiza con estadística descriptiva, una regresión lineal y gráficas.

**Objetivo académico:** que la aplicación funcione y, con la misma importancia, que el estudiante comprenda y pueda explicar con sus propias palabras cómo está construida, por qué se eligieron sus tecnologías, cómo circulan los datos y cuáles son las limitaciones del modelo.

## Qué hace

- Descarga de Open-Meteo un año móvil (hoy − 1 año → hoy) de:
  - temperatura a 2 m, humedad relativa a 2 m y viento a 10 m (reanálisis **ERA5**);
  - **PM2.5** (modelo **CAMS global**).
- Verifica la cobertura de los datos y descarga solo lo que falta.
- Guarda los datos en ObjectDB con su procedencia (qué descarga aportó cada valor).
- Calcula estadísticas descriptivas, el perfil diurno y franjas de mañana, tarde y noche (hora de Medellín).
- Entrena y evalúa una regresión lineal de PM2.5 a partir de temperatura, humedad y viento.
- Genera gráficas en una ventana o como PNG.

## Qué NO hace

- **No es un sistema de producción.** Está pensado para un solo usuario y una sola ejecución a la vez, sin servidor ni garantías de disponibilidad.
- **No es un pronóstico ambiental validado.** No predice la calidad del aire futura ni sustituye a la información oficial.
- **No usa mediciones de estaciones.** Todos los datos son de modelos; en particular, el PM2.5 son pronósticos archivados del modelo CAMS, no mediciones en Medellín.
- No usa redes neuronales ni modelos complejos.

## Estado actual

**Fase 0: documentación y diseño.** Todavía no hay código. El plan completo y el seguimiento están en [docs/fases.md](docs/fases.md). La siguiente fase es la **validación de las APIs** (Fase 1).

## Documentación

| Documento | Contenido |
|---|---|
| [docs/fases.md](docs/fases.md) | Plan de fases con objetivos, entregables, criterios de verificación y estado; tablas de decisiones pendientes y de puntos por verificar. |
| [docs/arquitectura.md](docs/arquitectura.md) | Flujo Python↔Java, protocolo de comunicación (subcomandos, stdout/stderr, JSON Lines), modelo de entidades y alternativas descartadas. |
| [docs/fuentes-y-datos.md](docs/fuentes-y-datos.md) | Fuentes de datos (ERA5, CAMS y alternativas), qué está verificado, limitaciones de los datos, licencia y atribución. |
| [docs/cobertura-y-franjas.md](docs/cobertura-y-franjas.md) | Ventana móvil, criterio de cobertura, cálculo de faltantes, actualización incremental y franjas horarias. |
| [docs/regresion.md](docs/regresion.md) | Modelo lineal, mínimos cuadrados, split temporal, Pipeline, métricas, línea base, diagnósticos y límites de interpretación. |
| [docs/cli-y-visualizaciones.md](docs/cli-y-visualizaciones.md) | Menú de la CLI, gráficas previstas, salida en ventana o PNG y mensajes en la terminal. |
| [docs/decisiones.md](docs/decisiones.md) | Registro de decisiones (D-001…) con contexto, opciones, consecuencias y estado. |
| [docs/glosario.md](docs/glosario.md) | Definiciones breves de los términos técnicos usados. |

## Plan de carpetas (previsto)

Esta es la estructura **planificada**; por ahora solo existen `README.md` y `docs/`. El detalle está en [docs/arquitectura.md](docs/arquitectura.md#estructura-de-directorios-prevista).

```text
clima-medellin/
├── README.md
├── docs/        documentación
├── python/      CLI, ingesta, análisis y gráficas
├── java/        entidades JPA y subcomandos del JAR (coverage, import, export)
├── data/        archivo de ObjectDB
├── staging/     lotes JSON Lines de Python hacia Java
├── exchange/    exportaciones JSON Lines de Java hacia Python
├── samples/     respuestas de las APIs de la Fase 1
└── outputs/     gráficas PNG
```

## Requisitos (previstos, por verificar)

| Componente | Previsto | Estado |
|---|---|---|
| Python | Versión 3 reciente | Por verificar (Fase 3) |
| Pandas, scikit-learn, Matplotlib | Versiones estables actuales | Por verificar (Fases 3, 7 y 8) |
| Cliente HTTP para Python | Por decidir | Por verificar (Fase 3) |
| Java | ≥ 8 (variante `javax` de ObjectDB) o ≥ 17 (variante `jakarta`) | Requisito verificado en la documentación de ObjectDB; versión instalada por verificar (Fase 2) |
| ObjectDB | 2.9.5, versión gratuita (máximo 10 clases de entidad y 1 millón de entidades por archivo) | Verificado en la documentación oficial; prueba práctica pendiente (Fase 2) |
| Conexión a internet | Acceso a las APIs de Open-Meteo (uso gratuito no comercial) | — |

## Principales limitaciones

- **Todo son modelos:** la meteorología es un reanálisis (ERA5, ~25 km) y el PM2.5 es un pronóstico archivado (CAMS global, ~45 km, paso de 3 h). Ninguno resuelve el valle de Aburrá ni equivale a una medición.
- **La regresión describe asociaciones entre modelos**, no causas ni la calidad del aire real.
- **La ventana es móvil:** los resultados cambian según la fecha de ejecución.
- **El paso de 3 h de PM2.5** obliga a revisar las franjas y la cobertura (decisiones pendientes de la Fase 1).

El detalle está en [docs/fuentes-y-datos.md](docs/fuentes-y-datos.md#limitaciones-de-los-datos).

## Atribución

Datos meteorológicos y de calidad del aire: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0), a partir de ERA5 (Copernicus Climate Change Service / ECMWF) y CAMS (Copernicus Atmosphere Monitoring Service). Ver [docs/fuentes-y-datos.md](docs/fuentes-y-datos.md#licencia-y-atribución).

## Limitaciones y supuestos

- Este README describe un proyecto en fase de diseño: los requisitos, las carpetas y los comandos son previstos y pueden cambiar.
- Las instrucciones de instalación y ejecución se añadirán en la Fase 9.
