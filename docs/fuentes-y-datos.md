# Fuentes y datos

Este documento describe de dónde vienen los datos, qué son exactamente (mediciones o modelos), qué se ha comprobado en la documentación oficial y qué falta por comprobar. Es la referencia del proyecto para las **limitaciones de los datos**: los demás documentos remiten aquí en lugar de repetirlas. Las decisiones que se apoyan en este documento son D-005, D-006, D-007, D-015 y D-022 ([decisiones.md](decisiones.md)).

Fecha de consulta de las fuentes oficiales: 2026-10-09.

## Idea central: todos los datos son de modelos

Antes de los detalles, lo más importante: **ninguno de los datos del proyecto es una medición de una estación en Medellín.**

- La temperatura, la humedad y el viento vienen de **ERA5**, un *reanálisis*: un modelo atmosférico corregido con observaciones del mundo entero. Para Medellín da el valor medio de una celda de unos 25 km × 25 km.
- El PM2.5 viene de **CAMS global**, un modelo de composición atmosférica. Lo que Open-Meteo ofrece como historial son **pronósticos archivados**, no mediciones ni un reanálisis [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)]. La celda mide unos 45 km.

Un ejemplo para hacerse una idea: el valle de Aburrá tiene unos 10 km de ancho en la zona urbana [Supuesto: orden de magnitud], así que una celda de 45 km incluye también montañas y zonas rurales. Si un martes hay un pico de contaminación en el centro por el tráfico, el modelo puede reflejarlo atenuado, desplazado en el tiempo o no reflejarlo.

## Tabla comparativa de fuentes

| Fuente | Qué es | Resolución espacial | Paso temporal | Disponibilidad | Retraso | Variables útiles | ¿Se usa? |
|---|---|---|---|---|---|---|---|
| **ERA5** | Reanálisis global (ECMWF / Copernicus) | 0,25° (~25 km) | 1 h | 1940 en adelante | 5 días | T, HR y viento a 10 m | **Sí** (D-005) |
| ERA5-Land | Reanálisis de superficie, forzado con ERA5 | 0,1° (~11 km) | 1 h | 1950 en adelante | 5 días | T y HR; **no da velocidad del viento** | No: falta el viento |
| ERA5-Seamless | Combinación de ERA5-Land (T, HR) y ERA5 (viento) | Mixta | 1 h | — | — | T, HR y viento | No: mezcla resoluciones en un mismo registro |
| ECMWF IFS | Análisis/pronóstico operativo de alta resolución | 9 km | 1 h | 2017 en adelante | Sin retraso; cada 6 h | T, HR y viento | No: no es un reanálisis homogéneo |
| *Best match* | Combinación automática de IFS HRES, ERA5 y ERA5-Land | Variable | 1 h | — | — | T, HR y viento | No: el modelo de origen puede cambiar dentro de la serie |
| **CAMS global** (Air Quality) | Pronósticos globales de composición atmosférica | 0,4° (~45 km) | 3 h | Agosto de 2022 en adelante | Actualización cada 12 h | PM2.5 | **Sí** (D-006) |
| CAMS Europa (Air Quality) | Pronóstico y reanálisis europeos | 0,1° (~11 km) | 1 h | Pronóstico desde octubre de 2023; reanálisis desde 2013 | 24 h | PM2.5 | No: solo cubre Europa |
| Estaciones de medición locales | Observaciones in situ (por ejemplo, la red de calidad del aire del valle de Aburrá) | Puntual | Típicamente 1 h [Supuesto] | [Por verificar] | [Por verificar] | PM2.5 medido | No: alternativa para una extensión futura |

Fuentes de la tabla: filas de ERA5, ERA5-Land, ERA5-Seamless, IFS y *best match* [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)]; filas de CAMS [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)]. La fila de estaciones locales no se ha verificado: solo se menciona como alternativa conceptual.

**Por qué ERA5 y no IFS, que tiene más resolución:** un reanálisis usa la misma versión del modelo para toda la serie, así que un cambio en los datos refleja un cambio en la atmósfera y no una actualización del software. IFS operativo cambia de versión con el tiempo [Supuesto]. Para una regresión sobre un año, la homogeneidad pesa más que la resolución [Recomendación].

## Detalle de las fuentes elegidas

### Meteorología: Open-Meteo Historical Weather API (ERA5)

| Aspecto | Valor | Estado |
|---|---|---|
| Endpoint base | `archive-api.open-meteo.com/v1/archive` | [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)] |
| Selección de modelo | La página lista ERA5 como opción; el valor del parámetro sería `era5` según la interfaz | [Por verificar, Fase 1: confirmar el nombre exacto del parámetro y su valor] |
| Variables | Temperatura a 2 m, humedad relativa a 2 m y velocidad del viento a 10 m | [Verificado: misma fuente] |
| Unidades por defecto | °C, %, km/h; el viento se puede pedir en m/s (`wind_speed_unit=ms`) | [Verificado: misma fuente] |
| Zona horaria por defecto | GMT; parámetro `timezone` opcional | [Verificado: misma fuente] |
| Elevación | Parámetro opcional para el reescalado estadístico; por defecto usa un modelo de elevación de 90 m; `nan` lo desactiva | [Verificado: misma fuente] |
| Retraso | «Daily with 5 days delay» | [Verificado: misma fuente] |
| Convención del timestamp | ¿Valor instantáneo a la hora indicada o agregado de la hora anterior? | [Por verificar, Fase 1] |
| Revisión de datos recientes | ¿Se revisan los últimos días o meses de ERA5 (versión preliminar)? | [Por verificar, Fase 1: comparar dos descargas separadas en el tiempo] |

### Calidad del aire: Open-Meteo Air Quality API (CAMS global)

| Aspecto | Valor | Estado |
|---|---|---|
| Endpoint base | `air-quality-api.open-meteo.com/v1/air-quality` | [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)] |
| Dominio | `domains=cams_global` (alternativas: `auto` y `cams_europe`) | [Verificado: misma fuente] |
| Variable | PM2.5 (`pm2_5`), µg/m³, instantáneo a 10 m sobre el suelo | [Verificado: misma fuente] |
| Resolución | 0,4° (~45 km), paso de 3 h | [Verificado: misma fuente] |
| Historial | Pronósticos archivados; dominio global desde agosto de 2022 | [Verificado: misma fuente] |
| Dominios acoplados | «The European and global domain are not coupled and may show different forecasts» | [Verificado: misma fuente] |
| Rango de fechas | Parámetros `start_date` y `end_date` (aaaa-mm-dd) | [Verificado: misma fuente] |
| **Paso real de la respuesta** | ¿La API devuelve 24 valores al día (interpolados) o 8 valores con `null` en medio? | **[Por verificar, Fase 1, crítico: afecta a D-006, D-009 y D-014]** |
| Un año completo para Medellín | Que una petición de 365 días devuelva datos sin huecos largos | [Por verificar, Fase 1] |
| Valores futuros | La respuesta incluye pronóstico (5 días por defecto); hay que recortarlo a la última hora pasada | [Verificado: existe el pronóstico; Recomendación: recortarlo] |

### Límites de uso

| Aspecto | Valor | Estado |
|---|---|---|
| Uso | API gratuita para uso no comercial, sin garantía de disponibilidad | [Verificado: [Open-Meteo – precios](https://open-meteo.com/en/pricing)] |
| Límites | 600/min, 5 000/h, 10 000/día, 300 000/mes | [Verificado: misma fuente] |
| Conteo | Más de 10 variables o más de 2 semanas para una ubicación cuentan como varias llamadas, de forma fraccionaria | [Verificado: misma fuente] |
| Estimación para este proyecto | Un año de 3 variables meteorológicas ≈ 52 semanas / 2 ≈ 26 llamadas equivalentes; otras ~26 para PM2.5 | [Supuesto: cálculo propio a partir de la regla anterior] |
| Tamaño máximo de rango por petición | No documentado | [Por verificar, Fase 1] |

Conclusión: una carga inicial completa consume menos del 1 % del límite diario. Los límites no son un problema práctico, pero la actualización incremental (D-015) sigue siendo buena práctica.

## Qué está verificado y qué no

**Verificado** (documentación oficial, 2026-10-09):

- Las resoluciones, pasos, disponibilidad y retrasos de ERA5, ERA5-Land, IFS y CAMS global/Europa de las tablas anteriores.
- ERA5-Land no ofrece velocidad del viento; *Best match* combina IFS HRES, ERA5 y ERA5-Land.
- PM2.5 en µg/m³ e instantáneo; el historial de calidad del aire son pronósticos archivados.
- Los límites de uso gratuito y la licencia CC BY 4.0.

**Por verificar** (todo en la Fase 1 salvo que se indique otra cosa):

1. Coordenadas del punto representativo y elevación que se fijará (D-007).
2. El parámetro y el valor exactos para forzar ERA5.
3. El paso real de PM2.5 en la respuesta (horario interpolado o cada 3 h).
4. Que haya un año completo de PM2.5 y de meteorología para Medellín.
5. El corte real de la latencia de ERA5 (¿hoy − 5 días con el día completo?).
6. La convención del timestamp de cada variable.
7. Si ERA5 revisa los datos recientes y si cambian los pronósticos archivados de CAMS.
8. La representación de los valores ausentes en las respuestas (`null`).
9. El rango máximo por petición.
10. El texto exacto de atribución para el dominio global de CAMS.

La lista consolidada, con su fase, está en [fases.md](fases.md#puntos-por-verificar).

## Limitaciones de los datos

### Modelados frente a observados

Como ya se dijo, todo viene de modelos. Consecuencias:

- **No se puede validar la calidad del aire real de Medellín con este proyecto.** Se analiza cómo se comporta el modelo CAMS en la celda que contiene a Medellín.
- CAMS usa como entrada su propia meteorología, del sistema IFS del ECMWF [Por verificar, Fase 1: confirmar en la documentación de CAMS]. Si es así, una regresión de PM2.5 (CAMS) sobre meteorología (ERA5) mide en parte **la coherencia interna entre dos productos del mismo centro**, no solo un fenómeno físico. Se discute en [regresion.md](regresion.md#limitaciones-de-interpretación).

### Resolución espacial

ERA5 (~25 km) y CAMS (~45 km) no resuelven el valle de Aburrá. La temperatura de la celda puede diferir de la del centro por la elevación media de la celda; Open-Meteo ofrece una corrección estadística por elevación (D-007), pero no la física del valle: inversiones térmicas, brisas de ladera y emisiones locales.

### Resolución temporal

ERA5 es horario; CAMS global tiene un paso de 3 horas. Los picos de PM2.5 de una o dos horas (por ejemplo, la hora punta de la mañana) no pueden representarse con fidelidad. Ver el tratamiento en [cobertura-y-franjas.md](cobertura-y-franjas.md#interacción-con-el-paso-de-3-horas-de-pm25).

### Latencia

ERA5 llega con 5 días de retraso. CAMS se actualiza cada 12 h, pero la API mezcla historial y pronóstico en la misma respuesta. Hay que recortar al pasado para no guardar pronósticos como si fueran historial (D-015).

### Cambios de modelo dentro de una serie

- **ERA5:** es homogéneo por diseño. Los datos más recientes podrían ser preliminares y revisarse [Por verificar, Fase 1].
- **CAMS:** al ser pronósticos operativos archivados, una mejora del modelo durante el año crea un salto artificial en la serie [Supuesto: el pronóstico operativo de CAMS se actualiza periódicamente; las fechas están por verificar en la Fase 1]. Una regresión no distingue un salto del modelo de un cambio real.
- Por eso se fija el modelo explícitamente (ERA5, `cams_global`) y no se usa *best match* ni `auto`.

### Cobertura geográfica

El dominio europeo de CAMS no cubre Colombia, así que solo sirve el global. ERA5 es global.

## Licencia y atribución

- **Open-Meteo:** los datos de la API se publican bajo **CC BY 4.0**. Hay que dar crédito e indicar las modificaciones; el ejemplo de atribución es «Weather data by Open-Meteo.com» con un enlace a open-meteo.com [Verificado: [Open-Meteo – licencia](https://open-meteo.com/en/licence) y [precios](https://open-meteo.com/en/pricing)].
- **Copernicus (C3S):** Open-Meteo lista al Copernicus Climate Change Service como origen del reanálisis y de los pronósticos de calidad del aire, con su propia licencia [Verificado: [Open-Meteo – licencia](https://open-meteo.com/en/licence)].
- **CAMS:** la página de calidad del aire exige «a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo» [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)]. La cita que da corresponde al dominio europeo; el texto exacto para el global está [Por verificar, Fase 1].
- **Citas académicas sugeridas por Open-Meteo:** Zippenfenig (2023), Open-Meteo.com Weather API, Zenodo, doi:10.5281/ZENODO.7970649; Hersbach et al. (2023), ERA5 hourly data on single levels, doi:10.24381/cds.adbb2d47 [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)].

**Aplicación en el proyecto** [Recomendación]: cada gráfica lleva una nota al pie con la fuente («Datos: Open-Meteo.com (ERA5, CAMS)»). El README y la memoria final incluyen la atribución completa.

## Fuentes oficiales citadas

- Open-Meteo, Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
- Open-Meteo, Air Quality API: https://open-meteo.com/en/docs/air-quality-api
- Open-Meteo, Pricing: https://open-meteo.com/en/pricing
- Open-Meteo, Licence: https://open-meteo.com/en/licence

(Las fuentes de ObjectDB se citan en [arquitectura.md](arquitectura.md#fuentes-consultadas).)

## Limitaciones y supuestos

- Toda la información de las fuentes viene de la documentación de Open-Meteo. No se han consultado directamente la documentación del ECMWF ni la de CAMS; las afirmaciones que dependen de ellas están marcadas como [Supuesto] o [Por verificar].
- Las cifras de resolución son nominales; el valor real en el punto depende de la malla y de la interpolación de Open-Meteo.
- La estimación de llamadas es aproximada y se basa en la regla de conteo publicada.
- La documentación puede cambiar; se consultó el 2026-10-09.
