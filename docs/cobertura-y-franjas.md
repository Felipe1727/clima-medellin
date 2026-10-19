# Cobertura y franjas horarias

Este documento define con precisión **qué datos se esperan**, cómo se mide si están (cobertura), cómo se decide qué descargar (actualización incremental) y cómo se resumen los datos horarios en **franjas** de mañana, tarde y noche. Son reglas que el estudiante debe poder aplicar a mano sobre un ejemplo pequeño. Las decisiones que se apoyan en este documento son D-008, D-009, D-013 a D-016 y D-021 ([decisiones.md](decisiones.md)).

## Ventana móvil

### Idea

El proyecto analiza siempre **el último año**. Si hoy es 9 de octubre de 2026, la ventana va del 9 de octubre de 2025 al 9 de octubre de 2026. Mañana se desplaza un día.

### Cálculo [Recomendación]

1. Fecha de referencia **D**: la fecha de hoy en America/Bogota (no en UTC; a las 21:00 de Medellín ya es el día siguiente en UTC).
2. **Inicio** = el mismo día y mes de D en el año anterior, a las 00:00 locales.
3. **Fin** = D a las 00:00 locales (exclusivo). El día de hoy no se incluye porque todavía está incompleto.
4. Ambos extremos se convierten a UTC: las 00:00 locales son las 05:00 UTC.
5. **Fin efectivo por fuente** = el mínimo entre el fin y el último dato publicado:
   - ERA5: unos 5 días antes de D [Verificado: retraso de 5 días, [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api)]. El corte exacto (si incluye o no el día D−5 completo) está [Por verificar, Fase 1].
   - CAMS: la última hora pasada. La API devuelve también horas futuras (pronóstico) que **no se guardan**.

### Caso del 29 de febrero

Si D es el 29 de febrero (por ejemplo, el 29-02-2028), «el mismo día del año anterior» no existe. Regla propuesta: **se usa el 28 de febrero** del año anterior (el último día válido de ese mes) [Recomendación, DP-09].

Consecuencia: la ventana no tiene siempre 365 días. Tiene 366 cuando incluye un 29 de febrero. Por eso **el número de horas esperadas se calcula a partir de la ventana real**, nunca se fija en 8 760.

| D (hoy) | Inicio | Días en la ventana |
|---|---|---|
| 2026-10-09 | 2025-10-09 | 365 |
| 2028-02-29 | 2027-02-28 | 366 |
| 2028-03-01 | 2027-03-01 | 366 (incluye el 29-02-2028) |
| 2029-03-01 | 2028-03-01 | 365 |

## Criterio de cobertura

### Métricas (por ubicación, fuente y variable)

| Métrica | Definición | Ejemplo |
|---|---|---|
| Pasos esperados | Timestamps que deberían existir entre el inicio y el fin efectivo, según el paso nativo de la fuente | 1 h en ERA5: 360 días × 24 = 8 640 |
| Pasos válidos | Timestamps con un valor no nulo de esa variable | 8 600 |
| Cobertura | válidos / esperados × 100 | 8 600 / 8 640 = 99,5 % |
| Hueco máximo | Duración del tramo consecutivo de faltantes más largo, en horas | 5 h |
| Número de huecos | Cantidad de tramos de faltantes | 12 |

La cobertura se mide **por variable** y no por registro: un WeatherRecord puede existir con la temperatura presente y el viento `null`.

### Estados

| Estado | Condición |
|---|---|
| **COMPLETA** | Todas las variables tienen cobertura ≥ 98 % **y** hueco máximo ≤ 6 h |
| **PARCIAL** | Hay al menos un valor, pero alguna variable no cumple la condición anterior |
| **SIN_DATOS** | No hay ningún registro de esa fuente en la ventana |

**Los umbrales del 98 % y de 6 h son decisiones de diseño (D-014), no estándares meteorológicos.** Su razonamiento:

- **98 %** de unas 8 760 horas permite unas 175 horas faltantes (algo más de 7 días sueltos). Es estricto pero alcanzable con un reanálisis, que en principio no tiene huecos [Supuesto].
- **6 h** de hueco máximo evita que los faltantes se concentren. En Medellín, un hueco de 6 h en la temperatura entre las 10:00 y las 15:59 locales borra justo el máximo diario; un hueco de 6 h por la noche borra el mínimo. Con huecos mayores se pierde el ciclo diario completo de ese día.

Los dos criterios se complementan: un 99 % de cobertura con un único hueco de 80 horas seguidas (más de 3 días) sería «casi completo» por porcentaje, pero inservible para analizar esos días.

### Interacción con el paso de 3 horas de PM2.5

El dominio global de CAMS tiene un paso nativo de 3 horas [Verificado: [Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)]. Cómo devuelve la API esos datos está **[Por verificar, Fase 1]**, y cada posibilidad tiene consecuencias distintas:

| Si la API devuelve… | Cobertura horaria de PM2.5 | Qué hacer [Recomendación] |
|---|---|---|
| 24 valores/día (interpolados) | ~100 %, pero 2 de cada 3 valores no son información nueva | Medir la cobertura sobre los pasos nativos y marcar los interpolados (DP-03) |
| 8 valores/día con `null` en medio | ~33 %: siempre PARCIAL con la regla horaria | Definir los «pasos esperados» de PM2.5 con un paso de 3 h; así la cobertura vuelve a tener sentido |

En ambos casos, la solución coherente es que **cada fuente tenga su propio paso esperado** en el cálculo de cobertura. Por eso D-006 y D-014 quedan como pendiente de revisión y provisional, respectivamente.

## Cálculo de faltantes e intervalos

### Intuición

Se comparan dos listas: la de los timestamps que **deberían** estar y la de los que **están**. La diferencia son los faltantes. Para no pedir hora a hora, los faltantes consecutivos se agrupan en intervalos, que se convierten en peticiones a la API.

### Pseudocódigo conceptual

(No es código ejecutable; describe los pasos.)

```text
ENTRADA: ubicación, fuente, paso_nativo, fecha_hoy_local, latencia_fuente
         timestamps_existentes  ← respuesta de Java «coverage»

1. inicio, fin ← ventana_móvil(fecha_hoy_local)               convertidos a UTC
2. fin_efectivo ← mínimo(fin, último_publicado(fuente, latencia_fuente))
3. esperados ← todos los instantes desde inicio hasta fin_efectivo (exclusivo),
               de paso_nativo en paso_nativo
4. faltantes ← esperados MENOS timestamps_existentes
5. Ordenar faltantes y recorrerlos:
     si el faltante actual es el siguiente al anterior (diferencia = paso_nativo)
         → amplía el intervalo abierto
     si no
         → cierra el intervalo y abre uno nuevo
6. Convertir cada intervalo a días completos (la API recibe fechas, no horas)
7. Unir los intervalos que, tras convertirlos a días, se tocan o solapan
8. Opcional: unir intervalos separados por pocos días si así se ahorran peticiones
9. SALIDA: lista de (fecha_inicio, fecha_fin) que se pedirán a la API
```

**Ejemplo pequeño.** Con ERA5, faltan las horas del 3 de marzo de 13:00 a 18:00 UTC y todo el 10 de marzo. El paso 5 produce dos intervalos. El paso 6 los convierte en «3 de marzo» y «10 de marzo». Se hacen dos peticiones de un día cada una. Las horas del 3 de marzo que ya existían llegarán otra vez, pero la clave natural las detecta como duplicadas y no se tocan (D-011, D-013).

Nota: los «timestamps existentes» que devuelve `coverage` son los que tienen registro. Un registro con todas sus variables a `null` **existe**, así que no se volverá a pedir. Si eso es deseable o si hay que volver a pedir esos valores se decide en la Fase 5 (DP-12) [Recomendación: no volver a pedirlos automáticamente; mostrarlos como hueco en la cobertura].

## Política de actualización incremental y de escritura

1. **Solo lo que falta.** Nunca se descarga el año completo si ya hay datos (D-015).
2. **Solo lo publicado.** No se piden fechas posteriores al fin efectivo de la fuente.
3. **Nunca el pronóstico.** De las respuestas de PM2.5 se descartan los timestamps posteriores a la hora actual.
4. **Solo inserciones.** Si un timestamp ya existe, se omite y se cuenta como duplicado. No se sobrescribe (D-013).
5. **Correcciones explícitas.** Un cambio de un valor existente solo es posible mediante un IngestionBatch de tipo CORRECCION, cuyo mecanismo se define en la Fase 2 (DP-04).
6. **Nada se borra por salir de la ventana.** Los datos de hace 13 meses siguen en la base; el análisis simplemente filtra por la ventana actual. A ~17 500 entidades por año, el límite gratuito de un millón tardaría décadas en alcanzarse [Supuesto: cálculo propio].
7. **Intentos vacíos.** Si la API no devuelve datos para un intervalo, se registra un IngestionBatch con 0 insertados. Así se sabe que el hueco es de la fuente y no un fallo del proceso [Recomendación].

## Franjas horarias

### Definición

| Franja | Hora central (hipótesis) | Ventana local | Timestamps locales incluidos | Equivalente en UTC |
|---|---|---|---|---|
| Mañana | 8:00 | 7–9 h | 07:00, 08:00, 09:00 | 12:00, 13:00, 14:00 (mismo día) |
| Tarde | 14:00 | 13–15 h | 13:00, 14:00, 15:00 | 18:00, 19:00, 20:00 (mismo día) |
| Noche | 20:00 | 19–21 h | 19:00, 20:00, 21:00 | 00:00, 01:00, 02:00 (**día siguiente**) |

[Supuesto] Las horas 8, 14 y 20 representan la hora punta de la mañana (capa de mezcla todavía baja), el máximo de calentamiento y el inicio de la noche. Son hipótesis que el perfil diurno de la Fase 6 debe confirmar o corregir.

### Zona horaria y cambios de fecha

- Los datos se guardan en UTC (D-008) y se convierten a America/Bogota **solo** para calcular franjas y perfiles.
- La franja de la noche del 5 de marzo local corresponde a las 00:00–02:00 UTC del **6 de marzo**. Si se agrupara por fecha UTC, esa franja quedaría asignada al día equivocado. Por eso **se agrupa por el día civil local**, después de convertir.
- Colombia no tiene horario de verano, así que no hay días de 23 ni de 25 horas [Por verificar en la base de datos tz, Fase 3]. Aun así, la conversión se hace con el nombre de la zona («America/Bogota») y no con un desfase fijo de −5, por robustez [Recomendación].

### Regla de mínimo de horas y NaN

- Cada franja de cada día y variable es el **promedio de los valores no nulos** de sus 3 horas.
- Si hay **menos de 2** valores válidos, la franja vale **NaN**.
- **No se interpola.** Un NaN es información: indica que ese día no hay suficientes datos para esa franja.
- Los análisis posteriores (medias por franja, comparaciones) ignoran los NaN y muestran cuántos días válidos hay por franja.

Ejemplo: el 12 de abril, la temperatura a las 07:00 es 17,8 °C, a las 08:00 falta y a las 09:00 es 19,6 °C. Hay 2 de 3 valores, así que la franja de la mañana vale 18,7 °C. Si también faltara el de las 09:00, valdría NaN.

**Pendiente de revisión (D-009):** si PM2.5 llega cada 3 horas, sus pasos nativos en hora local serían 19, 22, 1, 4, **7**, 10, **13** y 16 [Supuesto: pasos en 00, 03, …, 21 UTC; por verificar en la Fase 1]. Cada ventana (7–9, 13–15, 19–21) contiene **exactamente un** valor nativo, en su primera hora. Opciones a decidir en la Fase 6 (DP-01):

1. Para PM2.5, que la franja sea ese único valor nativo (mínimo de 1 de 1).
2. Desplazar las ventanas para centrarlas en los pasos nativos (6–8, 12–14, 18–20).
3. Aceptar los valores interpolados de la API, si existen, documentando que contradicen «no interpolar».

[Recomendación preliminar] La opción 1, que mantiene las mismas ventanas para las cuatro variables y no introduce valores inventados.

### Comparación: hora puntual frente a promedio por franja

| Criterio | Hora puntual (p. ej., 8:00) | Promedio de franja (7–9 h, mínimo 2/3) |
|---|---|---|
| Sencillez | Máxima | Algo mayor |
| Sensibilidad a un faltante | Un faltante → NaN | Tolera un faltante |
| Ruido | Mayor | Menor (promedia 3 valores) |
| Picos | Los conserva, si coinciden con la hora | Los suaviza |
| Desalineación con pasos de 3 h (PM2.5) | Puede caer siempre en un paso no nativo (las 8:00 locales no son paso nativo) | Contiene un paso nativo |

**Recomendación:** promedio por franja para la meteorología (más robusto y tolerante a faltantes) y, para PM2.5, el tratamiento que se decida en DP-01.

## Perfil diurno

El perfil diurno es la media de cada variable para cada hora local (0–23). Sirve para comprobar si las franjas elegidas capturan los momentos característicos del día.

- Se calcula **solo con el conjunto de entrenamiento** (ver [regresion.md](regresion.md#separación-temporal-con-hueco)). Si se usara todo el año y luego se eligieran las franjas o variables en función de él, el periodo de prueba influiría en el diseño (una forma de fuga de información).
- Se muestra con el número de valores válidos por hora, para no confundir una media con 300 datos y otra con 40.

## Limitaciones y supuestos

- Los umbrales del 98 % y de 6 h, la regla de 2 de 3 horas y las horas de las franjas son decisiones de diseño, no criterios estándar.
- La regla del 29 de febrero es una convención propuesta.
- El tratamiento de PM2.5 depende de un punto [Por verificar] crítico de la Fase 1 (paso real de la respuesta).
- Se supone que los timestamps de la API corresponden al inicio de la hora (instantáneos); si alguna variable fuera un agregado de la hora anterior, las franjas se desplazarían una hora [Por verificar, Fase 1].
- Las franjas en hora local no tienen en cuenta que el amanecer y el atardecer cambian algo a lo largo del año; en Medellín, cerca del ecuador, esa variación es pequeña [Supuesto].
