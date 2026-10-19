# Fuentes y datos

Este documento describe de dónde vienen los datos, qué son exactamente (mediciones o modelos), qué se ha comprobado en la documentación oficial y qué falta por comprobar. Es la referencia del proyecto para las **limitaciones de los datos**: los demás documentos remiten aquí en lugar de repetirlas. Las decisiones que se apoyan en este documento son D-005, D-006, D-007, D-015 y D-022 ([decisiones.md](decisiones.md)).

Fecha de consulta de las fuentes oficiales: 2026-10-09; revisión con peticiones reales (Fase 1): 2026-10-18. Las respuestas de muestra están en [`samples/`](../samples/README.md).

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
| Estaciones de medición locales | Observaciones in situ (por ejemplo, la red de calidad del aire del valle de Aburrá) | Puntual | Típicamente 1 h [Supuesto] | No se investiga (fuera del alcance) | No se investiga (fuera del alcance) | PM2.5 medido | No: alternativa para una extensión futura |

Fuentes de la tabla: filas de ERA5, ERA5-Land, ERA5-Seamless, IFS y *best match* [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)]; filas de CAMS [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)]. La fila de estaciones locales no se ha verificado: solo se menciona como alternativa conceptual.

**Por qué ERA5 y no IFS, que tiene más resolución:** un reanálisis usa la misma versión del modelo para toda la serie, así que un cambio en los datos refleja un cambio en la atmósfera y no una actualización del software. IFS operativo cambia de versión con el tiempo [Supuesto]. Para una regresión sobre un año, la homogeneidad pesa más que la resolución [Recomendación].

## Detalle de las fuentes elegidas

### Meteorología: Open-Meteo Historical Weather API (ERA5)

| Aspecto | Valor | Estado |
|---|---|---|
| Endpoint base | `archive-api.open-meteo.com/v1/archive` | [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)] |
| Selección de modelo | `models=era5`; la respuesta se ajusta a la celda de 0,25° (6,25, −75,5) | [Verificado: petición real, 2026-10-18] |
| Variables | Temperatura a 2 m, humedad relativa a 2 m y velocidad del viento a 10 m | [Verificado: misma fuente] |
| Unidades por defecto | °C, %, km/h; el viento se puede pedir en m/s (`wind_speed_unit=ms`) | [Verificado: misma fuente] |
| Zona horaria por defecto | GMT; parámetro `timezone` opcional | [Verificado: misma fuente] |
| Elevación | Parámetro opcional para el reescalado estadístico; por defecto usa un modelo de elevación de 90 m; `nan` lo desactiva. El proyecto envía `elevation=1495` (D-007) | [Verificado: misma fuente; la respuesta devuelve `elevation: 1495.0`] |
| Retraso | «Daily with 5 days delay». Con D = 2026-10-18, el último valor fue el de 2026-10-13 23:00 UTC: **el día D−5 llega completo** | [Verificado: misma fuente y petición real] |
| Días aún no publicados | La API **no los omite**: devuelve sus horas con `null` en todas las variables (96 nulos finales en la muestra) | [Verificado: `samples/era5_recent_month.json`] |
| Convención del timestamp | Temperatura, humedad y viento son **valores instantáneos** a la hora indicada (solo variables como la precipitación son agregados de la hora anterior) | [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)] |
| Revisión de datos recientes | Los últimos 2–3 meses de ERA5 son la versión preliminar **ERA5T**, que el ECMWF puede corregir al publicar la versión final. **El proyecto trata ERA5T como definitivo** (decisión de la exploración del 2026-10-18) | [Verificado: [ECMWF – ERA5T](https://forum.ecmwf.int/t/release-of-era5t/1136)] |

### Calidad del aire: Open-Meteo Air Quality API (CAMS global)

| Aspecto | Valor | Estado |
|---|---|---|
| Endpoint base | `air-quality-api.open-meteo.com/v1/air-quality` | [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)] |
| Dominio | `domains=cams_global` (alternativas: `auto` y `cams_europe`) | [Verificado: misma fuente] |
| Variable | PM2.5 (`pm2_5`), µg/m³, instantáneo a 10 m sobre el suelo | [Verificado: misma fuente] |
| Resolución | 0,4° (~45 km); la documentación indica paso de 3 h. En la respuesta, el punto del proyecto cae en la celda (6,2, −75,6) | [Verificado: misma fuente y petición real] |
| Historial | Pronósticos archivados; dominio global desde agosto de 2022 | [Verificado: misma fuente] |
| Dominios acoplados | «The European and global domain are not coupled and may show different forecasts» | [Verificado: misma fuente] |
| Rango de fechas | Parámetros `start_date` y `end_date` (aaaa-mm-dd) | [Verificado: misma fuente] |
| **Paso real de la respuesta** | **24 valores al día, sin ningún `null` en un año.** Las horas intermedias no son una interpolación de los pasos de 3 h (la curvatura es similar en todas las horas), así que se tratan como datos horarios. Ver [Empalmes de 00 y 12 UTC](#empalmes-de-las-ejecuciones-del-pronóstico-00-y-12-utc) | [Verificado: `samples/cams_pm25_year.json`] |
| Un año completo para Medellín | 8 760 valores horarios entre 2025-10-18 y 2026-10-17, sin huecos | [Verificado: misma muestra] |
| Validez temporal | PM2.5 es un valor **instantáneo** | [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)] |
| Elevación | La Air Quality API **no documenta** el parámetro `elevation`; el proyecto no lo envía | [Verificado: misma fuente] |
| Valores futuros | La respuesta incluye pronóstico (5 días por defecto); hay que recortarlo a la última hora pasada | [Verificado: existe el pronóstico; Recomendación: recortarlo] |

### Límites de uso

| Aspecto | Valor | Estado |
|---|---|---|
| Uso | API gratuita para uso no comercial, sin garantía de disponibilidad | [Verificado: [Open-Meteo – precios](https://open-meteo.com/en/pricing)] |
| Límites | 600/min, 5 000/h, 10 000/día, 300 000/mes | [Verificado: misma fuente] |
| Conteo | Más de 10 variables o más de 2 semanas para una ubicación cuentan como varias llamadas, de forma fraccionaria | [Verificado: misma fuente] |
| Estimación para este proyecto | Un año de 3 variables meteorológicas ≈ 52 semanas / 2 ≈ 26 llamadas equivalentes; otras ~26 para PM2.5 | [Supuesto: cálculo propio a partir de la regla anterior] |
| Tamaño máximo de rango por petición | No documentado. Una petición de un año completo funciona en una sola llamada para ambas APIs, así que el proyecto hace una petición por intervalo faltante, sin trocearla | [Verificado: petición real, 2026-10-18] |

Conclusión: una carga inicial completa consume menos del 1 % del límite diario. Los límites no son un problema práctico, pero la actualización incremental (D-015) sigue siendo buena práctica.

## Qué está verificado y qué no

**Verificado en la documentación oficial** (2026-10-09):

- Las resoluciones, pasos, disponibilidad y retrasos de ERA5, ERA5-Land, IFS y CAMS global/Europa de las tablas anteriores.
- ERA5-Land no ofrece velocidad del viento; *Best match* combina IFS HRES, ERA5 y ERA5-Land.
- PM2.5 en µg/m³ e instantáneo; el historial de calidad del aire son pronósticos archivados.
- Los límites de uso gratuito y la licencia CC BY 4.0.

**Verificado con peticiones reales en la Fase 1** (2026-10-18, muestras en [`samples/`](../samples/README.md)):

| ID | Punto | Resultado |
|---|---|---|
| PV-01 | Coordenadas del punto representativo | `MED-CENTRO`, centro de Medellín: 6,2447, −75,5748 (D-007). El punto exacto apenas importa: ERA5 lo ajusta a su celda (6,25, −75,5) y CAMS a la suya (6,2, −75,6). |
| PV-02 | Elevación fijada | 1 495 m (altitud oficial de la ciudad), enviada como `elevation=1495` a la API de ERA5. El modelo de elevación automático daba 1 493 m, así que el efecto del reescalado es prácticamente el mismo; la ventaja es que el valor es explícito y queda guardado en `Location`. |
| PV-03 | Parámetro para forzar ERA5 | `models=era5`. |
| PV-04 | Corte de la latencia de ERA5 | El día D−5 llega completo; el fin efectivo de ERA5 es las 00:00 UTC de D−4. |
| PV-05 | Paso real de PM2.5 | 24 valores horarios al día, sin nulos. Se tratan como datos horarios. |
| PV-06 | Un año completo disponible | Sí, para las dos fuentes (8 760 horas). |
| PV-07 | Revisiones de ERA5 reciente y cambios de versión de CAMS | ERA5T (últimos 2–3 meses) puede revisarse; el proyecto lo trata como definitivo y, al ser solo inserciones (D-013), conserva el primer valor. CAMS se actualiza aproximadamente una vez al año ([ECMWF – CAMS](https://confluence.ecmwf.int/display/CKB/CAMS:+Global+atmospheric+composition+forecast+data+documentation)); un cambio de versión dentro del año es una limitación documentada, no se corrige. |
| PV-08 | Convención del timestamp | Instantáneo a la hora indicada para las cuatro variables. |
| PV-09 | Representación de los ausentes | `null` en el JSON. En ERA5, los días aún no publicados llegan como horas con todas las variables a `null`. |
| PV-10 | Rango máximo por petición | No documentado; un año completo funciona en una sola petición. |
| PV-11 | Atribución de CAMS global | Ver [Licencia y atribución](#licencia-y-atribución). |
| PV-12 | CAMS usa meteorología del ECMWF | Sí: el pronóstico global de CAMS se ejecuta con el IFS, el mismo sistema que produce los pronósticos meteorológicos del ECMWF, con módulos añadidos de aerosoles y gases ([ECMWF – CAMS](https://confluence.ecmwf.int/display/CKB/CAMS:+Global+atmospheric+composition+forecast+data+documentation)). |

La lista consolidada está en [fases.md](fases.md#puntos-por-verificar).

## Hallazgos de la Fase 1

### Resumen de las muestras

| Variable | Muestra | Nulos | Mínimo | Media | Máximo |
|---|---|---|---|---|---|
| Temperatura a 2 m (°C) | `era5_year.json` | 96 (días finales no publicados) | 15,5 | 21,3 | 30,4 |
| Humedad relativa a 2 m (%) | `era5_year.json` | 96 | 42 | 83,3 | 100 |
| Viento a 10 m (m/s) | `era5_year.json` | 96 | 0,0 | 0,8 | 3,1 |
| PM2.5 (µg/m³) | `cams_pm25_year.json` | 0 | 0,8 | 12,9 (mediana 10,6; p95 29,3) | 49,9 |

### Empalmes de las ejecuciones del pronóstico (00 y 12 UTC)

El archivo de CAMS se construye encadenando pronósticos sucesivos: uno que empieza a las 00 UTC y otro a las 12 UTC. Cuando el siguiente toma el relevo, el valor salta. En la muestra anual, el **salto absoluto medio** entre una hora y la anterior es:

| Hora UTC de llegada | Salto medio (µg/m³) |
|---|---|
| **00** | **7,43** |
| **12** | **5,60** |
| Resto de horas | 1,31 de media (máximo 2,58, a la 01) |

Es decir, a las 00 y a las 12 UTC el salto es entre 4 y 6 veces mayor que en cualquier otra hora. **Es una costura del archivo, no un cambio de la atmósfera.** Consecuencias:

- En hora de Medellín, 00 UTC son las 19:00 y 12 UTC son las 07:00: la **franja de la mañana (07–09)** y la **de la noche (19–21)** empiezan justo en un empalme. Una diferencia de PM2.5 entre la mañana y la noche puede deberse en parte a dónde se empalman los pronósticos ([cobertura-y-franjas.md](cobertura-y-franjas.md#pm25-horario-y-empalmes-del-pronóstico)).
- La regresión usa todas las horas; los empalmes añaden ruido que el modelo no puede explicar con la meteorología ([regresion.md](regresion.md#limitaciones-de-interpretación)).
- **No se corrigen** (ni suavizado ni eliminación de horas): se documentan y se muestran en una gráfica de diagnóstico (salto medio por hora UTC, especificación `visualizations`).

## Limitaciones de los datos

### Modelados frente a observados

Como ya se dijo, todo viene de modelos. Consecuencias:

- **No se puede validar la calidad del aire real de Medellín con este proyecto.** Se analiza cómo se comporta el modelo CAMS en la celda que contiene a Medellín.
- CAMS se ejecuta con el sistema IFS del ECMWF, que también calcula su propia meteorología [Verificado: [ECMWF – CAMS](https://confluence.ecmwf.int/display/CKB/CAMS:+Global+atmospheric+composition+forecast+data+documentation)]. Por eso una regresión de PM2.5 (CAMS) sobre meteorología (ERA5) mide en parte **la coherencia interna entre dos productos del mismo centro**, no solo un fenómeno físico. Se discute en [regresion.md](regresion.md#limitaciones-de-interpretación).

### Resolución espacial

ERA5 (~25 km) y CAMS (~45 km) no resuelven el valle de Aburrá. La temperatura de la celda puede diferir de la del centro por la elevación media de la celda; Open-Meteo ofrece una corrección estadística por elevación (D-007), pero no la física del valle: inversiones térmicas, brisas de ladera y emisiones locales.

### Resolución temporal

ERA5 es horario. La documentación de CAMS global indica un paso de 3 horas, pero la API devuelve 24 valores horarios que no son una interpolación simple; el proyecto los trata como datos horarios (DP-01, DP-02, DP-03). Aun así, con celdas de ~45 km los picos de PM2.5 de una o dos horas (por ejemplo, la hora punta de la mañana) no pueden representarse con fidelidad, y los empalmes de 00 y 12 UTC añaden saltos artificiales ([Hallazgos de la Fase 1](#empalmes-de-las-ejecuciones-del-pronóstico-00-y-12-utc)).

### Latencia

ERA5 llega con 5 días de retraso y devuelve los días no publicados como `null`: la ingesta recorta en el fin efectivo antes de guardar, para que esas horas vacías no se tomen por datos existentes. CAMS se actualiza cada 12 h, pero la API mezcla historial y pronóstico en la misma respuesta; nada posterior al fin de la ventana se guarda (D-015).

### Cambios de modelo dentro de una serie

- **ERA5:** es homogéneo por diseño. Los últimos días de ERA5 son la versión preliminar ERA5T y se tratan como definitivos.
- **CAMS:** al ser pronósticos operativos archivados, una mejora del modelo durante el año crea un salto artificial en la serie. El sistema se actualiza aproximadamente una vez al año [Verificado: [ECMWF – CAMS](https://confluence.ecmwf.int/display/CKB/CAMS:+Global+atmospheric+composition+forecast+data+documentation)]. Una regresión no distingue un salto del modelo de un cambio real.
- Por eso se fija el modelo explícitamente (ERA5, `cams_global`) y no se usa *best match* ni `auto`.

### Cobertura geográfica

El dominio europeo de CAMS no cubre Colombia, así que solo sirve el global. ERA5 es global.

## Rangos plausibles

Antes de guardar, la ingesta convierte en `null` (y cuenta) los valores físicamente imposibles. Los rangos son **amplios a propósito**: no buscan valores raros, solo errores evidentes; nunca se sustituye un valor por otro inventado (D-012).

| Variable | Rango aceptado | Motivo | Valores reales en la muestra anual |
|---|---|---|---|
| Temperatura a 2 m | −20 … 50 °C | Muy por fuera de lo posible en Medellín (≈ 1 500 m de altitud) | 15,5 … 30,4 °C |
| Humedad relativa a 2 m | 0 … 100 % | Definición de humedad relativa | 42 … 100 % |
| Viento a 10 m | 0 … 75 m/s | Una velocidad negativa no existe; 75 m/s supera un huracán de categoría 5 | 0,0 … 3,1 m/s |
| PM2.5 | 0 … 1 000 µg/m³ | Una concentración negativa no existe; 1 000 µg/m³ supera los peores episodios de humo | 0,8 … 49,9 µg/m³ |

Los rangos están definidos en `python/src/clima_medellin/config.py` y se aplican en `normalize.py` ([implementacion.md](implementacion.md#34-validar-sin-inventar-valores-where-duplicados-y-recortes)).

## Licencia y atribución

- **Open-Meteo:** los datos de la API se publican bajo **CC BY 4.0**. Hay que dar crédito e indicar las modificaciones; el ejemplo de atribución es «Weather data by Open-Meteo.com» con un enlace a open-meteo.com [Verificado: [Open-Meteo – licencia](https://open-meteo.com/en/licence) y [precios](https://open-meteo.com/en/pricing)].
- **Copernicus (C3S):** Open-Meteo lista al Copernicus Climate Change Service como origen del reanálisis y de los pronósticos de calidad del aire, con su propia licencia [Verificado: [Open-Meteo – licencia](https://open-meteo.com/en/licence)].
- **CAMS:** la página de calidad del aire exige «a clear attribution to CAMS ENSEMBLE data provider as well as a reference to Open-Meteo» [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)]. La cita que da corresponde al dominio europeo y no hay una específica para el global. **Texto adoptado por el proyecto para el dominio global:** «Datos de calidad del aire: CAMS global atmospheric composition forecasts (Copernicus Atmosphere Monitoring Service), vía Open-Meteo.com» [Recomendación: combina el producto real usado con la referencia a Open-Meteo que exige la página].
- **Citas académicas sugeridas por Open-Meteo:** Zippenfenig (2023), Open-Meteo.com Weather API, Zenodo, doi:10.5281/ZENODO.7970649; Hersbach et al. (2023), ERA5 hourly data on single levels, doi:10.24381/cds.adbb2d47 [Verificado: [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)].

**Aplicación en el proyecto** [Recomendación]: cada gráfica lleva una nota al pie con la fuente («Datos: Open-Meteo.com (ERA5, CAMS)»). El README y la memoria final incluyen la atribución completa.

## Fuentes oficiales citadas

- Open-Meteo, Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
- Open-Meteo, Air Quality API: https://open-meteo.com/en/docs/air-quality-api
- Open-Meteo, Pricing: https://open-meteo.com/en/pricing
- Open-Meteo, Licence: https://open-meteo.com/en/licence

(Las fuentes de ObjectDB se citan en [arquitectura.md](arquitectura.md#fuentes-consultadas).)

## Limitaciones y supuestos

- La información de las fuentes viene de la documentación de Open-Meteo y, para ERA5T y el modelo de CAMS, de la documentación del ECMWF; los hallazgos de la Fase 1 proceden de las muestras guardadas en `samples/`.
- Las cifras de resolución son nominales; el valor real en el punto depende de la malla y de la interpolación de Open-Meteo.
- La estimación de llamadas es aproximada y se basa en la regla de conteo publicada.
- La documentación puede cambiar; se consultó el 2026-10-09 y se revisó el 2026-10-18.
