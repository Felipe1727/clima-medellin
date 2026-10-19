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
   - ERA5: **las 00:00 UTC de D−4** (exclusivo): el día D−5 llega completo [Verificado: petición real del 2026-10-18; con D = 2026-10-18 el último valor fue el de 2026-10-13 23:00 UTC]. La API devuelve los días posteriores como horas con todas las variables a `null`; la ingesta las descarta antes de guardar.
   - CAMS: el fin de la ventana. La API devuelve también horas futuras (pronóstico) que **no se guardan**.
   - Nada en el fin efectivo o después de él se guarda nunca.

### Caso del 29 de febrero

Si D es el 29 de febrero (por ejemplo, el 29-02-2028), «el mismo día del año anterior» no existe. Regla adoptada: **se usa el 28 de febrero** del año anterior (el último día válido de ese mes) (DP-09, implementada en `coverage.one_year_before`).

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
| Pasos esperados | Timestamps que deberían existir entre el inicio y el fin efectivo, con paso horario en las dos fuentes (DP-03) | 1 h en ERA5: 360 días × 24 = 8 640 |
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

### PM2.5: pasos esperados horarios

La documentación del dominio global de CAMS indica un paso nativo de 3 horas, pero la API devuelve **24 valores horarios al día, sin nulos**, que no son una interpolación simple [Verificado: `samples/cams_pm25_year.json`, Fase 1]. Por eso **PM2.5 usa pasos esperados horarios, igual que ERA5** (DP-03): con un año completo, su cobertura es del 100 % y los umbrales de D-014 se aplican sin cambios.

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

Nota: los «timestamps existentes» que devuelve `coverage` son los que tienen registro. **Nunca se guarda una fila con todas sus variables a `null`** (DP-12): Python la descarta antes de entregar el lote a Java. Así, «existe un registro» significa «hay al menos un valor real», y una hora sin ningún dato sigue contando como faltante y se vuelve a pedir en la siguiente actualización, lo cual es barato. Las filas con solo algunas variables a `null` sí se guardan, con esos valores a `null` (D-012).

## Política de actualización incremental y de escritura

1. **Solo lo que falta.** Nunca se descarga el año completo si ya hay datos (D-015).
2. **Solo lo publicado.** No se piden fechas posteriores al fin efectivo de la fuente.
3. **Nunca el pronóstico.** De las respuestas de PM2.5 se descartan los timestamps en o después del fin de la ventana (las 00:00 locales de hoy), que ya es pasado; así nunca se guarda una hora de pronóstico.
   - **Solo dentro de la ventana.** La API recibe días UTC completos, así que la primera petición empieza a las 00:00 UTC, cinco horas antes de la ventana (05:00 UTC); esas horas se descartan antes de importar.
4. **Solo inserciones.** Si un timestamp ya existe, se omite y se cuenta como duplicado. No se sobrescribe (D-013).
5. **Sin correcciones.** Un valor guardado no cambia nunca; el proyecto no implementa lotes de corrección (DP-04). Los datos recientes de ERA5 (ERA5T) se tratan como definitivos.
6. **Nada se borra por salir de la ventana.** Los datos de hace 13 meses siguen en la base; el análisis simplemente filtra por la ventana actual. A ~17 500 entidades por año, el límite gratuito de un millón tardaría décadas en alcanzarse [Supuesto: cálculo propio].
7. **Intentos vacíos.** Si la API no devuelve datos para un intervalo, se registra un IngestionBatch con 0 insertados. Así se sabe que el hueco es de la fuente y no un fallo del proceso. Implementado: `update.execute_plan` importa también los lotes vacíos.

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
- Colombia no tiene horario de verano, así que no hay días de 23 ni de 25 horas [Verificado: la base de datos tz da UTC−5 en todas las horas de 2025 y 2026, Fase 3]. Aun así, la conversión se hace con el nombre de la zona («America/Bogota») y no con un desfase fijo de −5, por robustez [Recomendación].

### Regla de mínimo de horas y NaN

- Cada franja de cada día y variable es el **promedio de los valores no nulos** de sus 3 horas.
- Si hay **menos de 2** valores válidos, la franja vale **NaN**.
- **No se interpola.** Un NaN es información: indica que ese día no hay suficientes datos para esa franja.
- Los análisis posteriores (medias por franja, comparaciones) ignoran los NaN y muestran cuántos días válidos hay por franja.

Ejemplo: el 12 de abril, la temperatura a las 07:00 es 17,8 °C, a las 08:00 falta y a las 09:00 es 19,6 °C. Hay 2 de 3 valores, así que la franja de la mañana vale 18,7 °C. Si también faltara el de las 09:00, valdría NaN.

### PM2.5 horario y empalmes del pronóstico

Como PM2.5 llega con valores horarios (ver [PM2.5: pasos esperados horarios](#pm25-pasos-esperados-horarios)), **la regla de franjas es la misma para las 4 variables** (DP-01): promedio de los valores no nulos de las 3 horas y NaN si hay menos de 2.

**Advertencia sobre los empalmes.** El archivo de CAMS encadena pronósticos que empiezan a las 00 y a las 12 UTC, y en esas horas el valor salta mucho más que en el resto (salto medio de 7,4 y 5,6 µg/m³ frente a 1,3; ver [fuentes-y-datos.md](fuentes-y-datos.md#empalmes-de-las-ejecuciones-del-pronóstico-00-y-12-utc)). En hora local:

| Franja | Ventana local | Ventana UTC | Empalme |
|---|---|---|---|
| Mañana | 07–09 | 12–14 | **Empieza en el empalme de 12 UTC** |
| Tarde | 13–15 | 18–20 | Ninguno |
| Noche | 19–21 | 00–02 (día siguiente) | **Empieza en el empalme de 00 UTC** |

Una diferencia de PM2.5 entre la mañana o la noche y la tarde puede deberse en parte a dónde se empalman los pronósticos y no a la calidad del aire. Los empalmes **no se corrigen** (no se suaviza ni se eliminan horas): se documentan y se muestran en una gráfica de diagnóstico, y deben tenerse en cuenta al interpretar las franjas de PM2.5.

### Comparación: hora puntual frente a promedio por franja

| Criterio | Hora puntual (p. ej., 8:00) | Promedio de franja (7–9 h, mínimo 2/3) |
|---|---|---|
| Sencillez | Máxima | Algo mayor |
| Sensibilidad a un faltante | Un faltante → NaN | Tolera un faltante |
| Ruido | Mayor | Menor (promedia 3 valores) |
| Picos | Los conserva, si coinciden con la hora | Los suaviza |
| Empalmes del pronóstico de CAMS (PM2.5) | Las 07:00 y 19:00 locales caen justo en un empalme | El empalme pesa un tercio del promedio |

**Decisión:** promedio por franja para las 4 variables (más robusto y tolerante a faltantes), con la advertencia de los empalmes para PM2.5 (DP-01).

## Perfil diurno

El perfil diurno es la media de cada variable para cada hora local (0–23). Sirve para comprobar si las franjas elegidas capturan los momentos característicos del día.

- Se calcula **solo con el conjunto de entrenamiento** (ver [regresion.md](regresion.md#separación-temporal-con-hueco)). Si se usara todo el año y luego se eligieran las franjas o variables en función de él, el periodo de prueba influiría en el diseño (una forma de fuga de información).
- Se muestra con el número de valores válidos por hora, para no confundir una media con 300 datos y otra con 40.

## Limitaciones y supuestos

- Los umbrales del 98 % y de 6 h, la regla de 2 de 3 horas y las horas de las franjas son decisiones de diseño, no criterios estándar.
- La regla del 29 de febrero es una convención del proyecto (DP-09).
- La implementación (Fase 5) está en `python/src/clima_medellin/coverage.py` y `update.py`, explicada en [implementacion.md](implementacion.md#5-ventana-móvil-cobertura-e-intervalos-faltantes).
- PM2.5 se trata como horario porque así lo entrega la API (Fase 1); sus empalmes de 00 y 12 UTC afectan a las franjas de la mañana y de la noche.
- Las cuatro variables son valores instantáneos a la hora indicada [Verificado: documentación de Open-Meteo, Fase 1], así que las franjas no se desplazan.
- Las franjas en hora local no tienen en cuenta que el amanecer y el atardecer cambian algo a lo largo del año; en Medellín, cerca del ecuador, esa variación es pequeña [Supuesto].
