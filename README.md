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

**Implementado.** Las fases 0 a 9 de [docs/fases.md](docs/fases.md) están completas: descarga incremental, persistencia en ObjectDB, cobertura, franjas, estadísticas, regresión, gráficas y el menú de 7 opciones, con pruebas automáticas (JUnit y pytest) e integración continua. La guía técnica del código está en [docs/implementacion.md](docs/implementacion.md); el orden de implementación, en [openspec/roadmap.md](openspec/roadmap.md).

## Instalación

Requisitos previos: **Java 25** (JDK), **Maven 3.9** y **[uv](https://docs.astral.sh/uv/)**. uv descarga por sí mismo Python 3.14 si no está instalado.

```bash
git clone https://github.com/Felipe1727/clima-medellin.git
cd clima-medellin

# 1. Compilar el JAR de persistencia (descarga ObjectDB de su repositorio Maven)
cd java && mvn -q -DskipTests package && cd ..

# 2. Crear el entorno de Python e instalar dependencias y el comando clima-medellin
cd python && uv sync && cd ..
```

Comprobación: `cd python && uv run clima-medellin --version` imprime `clima-medellin 0.1.0`.

## Uso

```bash
cd python
uv run clima-medellin            # abre el menú
uv run clima-medellin --verbose  # igual, mostrando también los mensajes del JAR de Java
```

```text
  CLIMA MEDELLÍN · Bases de Datos
  Ubicación: MED-CENTRO · Ventana: 2025-10-18 → 2026-10-18 (America/Bogota)

  1) Verificar cobertura
  2) Actualizar datos
  3) Consultar registros
  4) Estadísticas descriptivas
  5) Entrenar y evaluar la regresión
  6) Generar visualizaciones
  7) Salir
```

Primer uso: elige **2) Actualizar datos** y confirma con `s`; la carga inicial de un año son dos peticiones a Open-Meteo (unos segundos). Después, las opciones 1 y 3 a 6 trabajan con los datos guardados en `data/clima.odb`, y las gráficas en PNG se guardan en `outputs/`. Cada opción está descrita en [docs/cli-y-visualizaciones.md](docs/cli-y-visualizaciones.md).

Solo puede haber una ejecución a la vez: ObjectDB no permite que dos procesos abran la misma base.

## Pruebas

```bash
cd java && mvn -q verify && cd ../python && uv run pytest   # pruebas Java y Python
cd python && uv run ruff check .                            # estilo del código Python
```

Las pruebas no usan la red: trabajan con las respuestas reales guardadas en `samples/` y con bases temporales.

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
| [docs/implementacion.md](docs/implementacion.md) | Guía técnica de la implementación: llamadas a ObjectDB, inserción y consulta, puente Java↔Python, análisis y gráficas, con ejemplos y fragmentos reales del código verificados por las pruebas. |

## Estructura de carpetas

Las carpetas marcadas como *(se crea al ejecutar)* aparecen la primera vez que se usa la aplicación y no se versionan. El detalle está en [docs/arquitectura.md](docs/arquitectura.md#estructura-de-directorios-prevista).

```text
clima-medellin/
├── README.md
├── .github/workflows/  integración continua (instalar, probar, analizar)
├── docs/               documentación de diseño y guía técnica
├── openspec/           roadmap y especificaciones (OpenSpec)
├── java/               proyecto Maven: entidades JPA y subcomandos del JAR (coverage, import, export)
├── python/             proyecto uv: CLI, ingesta, análisis y gráficas (src/clima_medellin, tests)
├── samples/            respuestas de las APIs guardadas en la Fase 1
├── data/               archivo de ObjectDB (se crea al ejecutar)
├── staging/            lotes JSON Lines de Python hacia Java (se crea al ejecutar)
├── exchange/           exportaciones JSON Lines de Java hacia Python (se crea al ejecutar)
└── outputs/            gráficas PNG (se crea al ejecutar)
```

## Requisitos

| Componente | Versión | Estado |
|---|---|---|
| Python | 3.14 (gestionado con [uv](https://docs.astral.sh/uv/)) | Verificado: 3.14.7 (Fase 3) |
| Pandas, scikit-learn, statsmodels, Matplotlib | Versiones fijadas en `python/uv.lock` | Verificado: pandas 3.0.6, scikit-learn 1.9.1, statsmodels 0.15.0, Matplotlib 3.11.2 (Fase 3) |
| Cliente HTTP para Python | requests | Verificado: 2.34.2 (Fase 3) |
| Java | 25, con Maven 3.9 | Verificado (Fase 2) |
| ObjectDB | 2.9.5, variante `jakarta` (`objectdb-jk`), versión gratuita (máximo 10 clases de entidad y 1 millón de entidades por archivo) | Verificado con las pruebas de la Fase 2 |
| Conexión a internet | Acceso a las APIs de Open-Meteo (uso gratuito no comercial) | — |

## Principales limitaciones

- **Todo son modelos:** la meteorología es un reanálisis (ERA5, ~25 km) y el PM2.5 es un pronóstico archivado (CAMS global, ~45 km). Ninguno resuelve el valle de Aburrá ni equivale a una medición.
- **La regresión describe asociaciones entre modelos**, no causas ni la calidad del aire real.
- **La ventana es móvil:** los resultados cambian según la fecha de ejecución.
- **Los empalmes del pronóstico de CAMS** (00 y 12 UTC) producen saltos artificiales en PM2.5 justo al inicio de las franjas de la mañana y de la noche; se documentan y se muestran, pero no se corrigen.

El detalle está en [docs/fuentes-y-datos.md](docs/fuentes-y-datos.md#limitaciones-de-los-datos).

## Atribución

Datos meteorológicos y de calidad del aire: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0), a partir de ERA5 (Copernicus Climate Change Service / ECMWF) y CAMS (Copernicus Atmosphere Monitoring Service). Ver [docs/fuentes-y-datos.md](docs/fuentes-y-datos.md#licencia-y-atribución).

## Limitaciones y supuestos

- Las versiones de la tabla de requisitos son las usadas y probadas en el desarrollo (octubre de 2026).
- Los resultados numéricos documentados (cobertura, franjas, regresión) corresponden a la ventana del 2026-10-18; al ejecutar la aplicación otro día, la ventana móvil cambia y los números también.
