# Plan de fases de trabajo

Este es el documento central de seguimiento del proyecto. Divide el trabajo en fases numeradas y, para cada una, indica qué se busca, qué se entrega, qué conceptos se estudian, cómo se sabe que está bien hecha, de qué depende, qué decisiones abiertas se resuelven y en qué estado está. Al final se consolidan las decisiones pendientes y los puntos por verificar de todos los documentos.

**Leyenda de estado:** `[ ]` pendiente · `[~]` en curso · `[x]` completada.

## Vista general

| Fase | Nombre | Estado | Depende de |
|---|---|---|---|
| 0 | Documentación y diseño | [x] | — |
| 1 | Validación de las APIs | [ ] | 0 |
| 2 | Modelo de datos y persistencia en ObjectDB | [ ] | 0 |
| 3 | Ingesta y normalización en Python | [ ] | 1 |
| 4 | Puente Java↔Python | [ ] | 2, 3 |
| 5 | Cobertura histórica e incrementos | [ ] | 4 |
| 6 | Franjas horarias y estadística descriptiva | [ ] | 5 |
| 7 | Regresión lineal y evaluación | [ ] | 6 |
| 8 | Visualizaciones | [ ] | 6, 7 |
| 9 | CLI integrada, pruebas finales y defensa | [ ] | 1–8 |

Las fases 1 y 2 son independientes y pueden hacerse en paralelo.

---

## Fase 0 — Documentación y diseño

**Objetivo:** fijar por escrito la arquitectura, las fuentes, las reglas de cobertura y de franjas, el modelo estadístico y la interfaz, antes de escribir código, de modo que cada decisión esté justificada y cada duda identificada.

**Entregables:**
- [x] [README.md](../README.md)
- [x] [decisiones.md](decisiones.md), [glosario.md](glosario.md)
- [x] [fuentes-y-datos.md](fuentes-y-datos.md), [arquitectura.md](arquitectura.md)
- [x] [cobertura-y-franjas.md](cobertura-y-franjas.md), [regresion.md](regresion.md), [cli-y-visualizaciones.md](cli-y-visualizaciones.md)
- [x] Este plan de fases
- [x] Lectura y revisión completa por parte del estudiante, y respuesta a las decisiones pendientes que dependan de su criterio (sesión de exploración del 2026-10-18; resultado en [openspec/roadmap.md](../openspec/roadmap.md))
- [x] Esqueleto del proyecto: proyectos Maven (`java/`) y uv (`python/`), integración continua y [implementacion.md](implementacion.md)

**Conceptos que se estudiarán:**
- *Reanálisis frente a observación*: entender qué representa cada dato antes de usarlo.
- *Registro de decisiones (ADR)*: dejar trazado el porqué de cada elección para poder defenderla.
- *Separación de responsabilidades*: cada proceso (Python, Java) tiene un papel claro.

**Criterio de verificación:** el estudiante puede explicar, sin leer, el diagrama de [arquitectura.md](arquitectura.md#diagrama-del-flujo-completo), por qué PM2.5 es un modelo y por qué el split es temporal; y puede responder las preguntas de [regresion.md](regresion.md#preguntas-de-comprobación).

**Dependencias:** ninguna.

**Decisiones abiertas:** ninguna se resuelve aquí; todas se asignan a fases posteriores (ver la [tabla final](#decisiones-pendientes)).

**Estado:** [x] completada.

---

## Fase 1 — Validación de las APIs

**Objetivo:** confirmar con peticiones reales que Open-Meteo entrega lo que suponemos para Medellín, antes de construir nada encima. Solo exploración: peticiones manuales (navegador o herramienta HTTP) y respuestas guardadas en `samples/`, **sin código de producción**.

**Entregables:**
- [ ] Coordenadas y elevación del punto representativo elegidas y justificadas (PV-01, PV-02).
- [ ] Respuestas de muestra guardadas en `samples/`: ERA5 para un año y para un mes reciente; PM2.5 para un año y para la última semana.
- [ ] Una nota de hallazgos, en la que se actualiza [fuentes-y-datos.md](fuentes-y-datos.md): paso real de PM2.5, latencia observada, unidades, nulos, convención del timestamp y atribución.
- [ ] D-005, D-006 y D-009 actualizadas en [decisiones.md](decisiones.md).

**Conceptos que se estudiarán:**
- *Parámetros de una API REST*: cómo se expresa una consulta en la URL.
- *Estructura de la respuesta JSON de Open-Meteo*: listas paralelas de tiempos y valores.
- *Paso temporal nativo frente a paso de salida*: saber si un dato es real o interpolado.
- *Latencia de publicación*: hasta qué fecha se puede pedir.
- *Licencia CC BY 4.0*: obligaciones de atribución.

**Criterio de verificación:**
- Una petición de 365 días de ERA5 devuelve unos 8 760 valores por variable, con el porcentaje de nulos anotado.
- Se sabe con certeza, a partir de una muestra, si PM2.5 llega cada hora o cada 3 horas y si hay `null`.
- La fecha del último dato de ERA5 se ha comparado con la fecha de la petición.

**Dependencias:** Fase 0.

**Decisiones abiertas:** DP-01 (franjas y PM2.5, se prepara aquí), DP-02 (resolución de PM2.5 en la regresión, se prepara aquí), DP-11 (ubicación).

**Estado:** [ ] pendiente.

---

## Fase 2 — Modelo de datos y persistencia en ObjectDB

**Objetivo:** comprobar que ObjectDB, con JPA, guarda las cuatro entidades, impide duplicados por la clave natural y conserva los datos tras cerrar y reabrir la base.

**Entregables:**
- [ ] Versión de Java instalada y variante de ObjectDB (`javax` o `jakarta`) elegidas (DP-07).
- [ ] Entidades Location, WeatherRecord, AirQualityRecord e IngestionBatch definidas según [arquitectura.md](arquitectura.md#modelo-de-clases).
- [ ] Prueba documentada: insertar, intentar un duplicado, cerrar, reabrir y consultar.
- [ ] Mecanismo de lote de corrección decidido (DP-04).

**Conceptos que se estudiarán:**
- *Entidad y EntityManager*: cómo JPA convierte objetos en registros persistentes.
- *Transacción*: garantizar que un lote se guarda entero o no se guarda.
- *Índice único compuesto*: implementar la clave natural en la base.
- *Relaciones muchos a uno*: enlazar un registro con su ubicación y su lote.
- *Tipos que admiten null*: representar los ausentes (D-012).

**Criterio de verificación:**
- Insertar dos veces el mismo (ubicación, fuente, timestamp) deja un solo registro y el segundo intento queda contado como duplicado, sin abortar el resto.
- Tras reabrir la base, los conteos coinciden.
- Un valor `null` se guarda y se recupera como null, no como 0.

**Dependencias:** Fase 0. Puede hacerse en paralelo a la Fase 1.

**Decisiones abiertas:** DP-04, DP-07; se confirma D-010 y la implementación de D-011.

**Estado:** [ ] pendiente.

---

## Fase 3 — Ingesta y normalización en Python

**Objetivo:** convertir una respuesta de la API en un DataFrame limpio y validado, listo para entregarse a Java.

**Entregables:**
- [ ] Cliente HTTP para las dos APIs con los parámetros fijados en la Fase 1.
- [ ] Normalización: timestamps UTC, unidades canónicas (DP-06), validación de rangos, duplicados y nulos.
- [ ] Reglas de rangos plausibles documentadas (por ejemplo, la humedad entre 0 y 100 %).
- [ ] Pruebas con las muestras de `samples/` (sin red).

**Conceptos que se estudiarán:**
- *DataFrame e índice temporal*: estructura central del análisis.
- *Zonas horarias en Pandas*: convertir entre UTC y America/Bogota sin errores.
- *Validación de rangos*: detectar valores imposibles sin inventar reemplazos.
- *NaN frente a 0*: mantener la semántica de los ausentes.
- *Manejo de errores HTTP*: reintentos y mensajes claros.

**Criterio de verificación:** a partir de una muestra guardada, el DataFrame tiene el número esperado de filas, ningún timestamp duplicado, unidades correctas y los nulos preservados. Un valor fuera de rango insertado a mano en una copia de la muestra se detecta.

**Dependencias:** Fase 1 (parámetros y formato reales).

**Decisiones abiertas:** DP-06 (unidad del viento); PV-16 (zona horaria).

**Estado:** [ ] pendiente.

---

## Fase 4 — Puente Java↔Python

**Objetivo:** implementar el protocolo de [arquitectura.md](arquitectura.md#protocolo-de-comunicación) y demostrar una ida y vuelta completa sin pérdida de información.

**Entregables:**
- [ ] JAR con los subcomandos `coverage`, `import` y `export`.
- [ ] Formato JSON Lines definitivo para `staging/` y `exchange/`.
- [ ] Tabla de códigos de salida definitiva (DP-05).
- [ ] Política de limpieza de `staging/` y `exchange/`.
- [ ] Prueba de ida y vuelta: DataFrame → `staging/` → `import` → `export` → `exchange/` → DataFrame idéntico.

**Conceptos que se estudiarán:**
- *Procesos hijo, stdout, stderr y código de salida*: el contrato entre dos programas.
- *JSON Lines*: serialización registro a registro.
- *Idempotencia*: importar el mismo lote dos veces no cambia la base.

**Criterio de verificación:**
- La ida y vuelta conserva los valores, los nulos y los timestamps.
- Importar dos veces el mismo archivo inserta 0 registros la segunda vez.
- Un JSON corrupto produce el código de error de datos y un mensaje claro en Python.
- stdout contiene solo JSON en todos los casos.

**Dependencias:** Fases 2 y 3.

**Decisiones abiertas:** DP-05; PV-15 (bloqueo del archivo).

**Estado:** [ ] pendiente.

---

## Fase 5 — Cobertura histórica e incrementos

**Objetivo:** calcular la cobertura de la ventana móvil y descargar solo lo que falta, respetando la latencia de cada fuente.

**Entregables:**
- [ ] Cálculo de la ventana (incluido el 29 de febrero), del fin efectivo por fuente y de los intervalos faltantes, según [cobertura-y-franjas.md](cobertura-y-franjas.md).
- [ ] Estados COMPLETA, PARCIAL y SIN_DATOS con umbrales confirmados (DP-03).
- [ ] Carga inicial completa de un año en la base.
- [ ] Prueba incremental: borrar un día en una base de prueba (o empezar con un hueco) y comprobar que solo se pide ese día.

**Conceptos que se estudiarán:**
- *Ventana móvil*: periodo que se desplaza con la fecha actual.
- *Conjuntos esperados frente a existentes*: cómo se obtienen los faltantes.
- *Agrupación de intervalos*: minimizar peticiones.
- *Latencia de publicación*: no pedir lo que aún no existe.

**Criterio de verificación:** tras la carga inicial, el estado es COMPLETA (o PARCIAL con una causa conocida de la fuente). Una segunda actualización inmediata no descarga nada. Ninguna hora futura de PM2.5 aparece en la base.

**Dependencias:** Fase 4.

**Decisiones abiertas:** DP-03, DP-09, DP-12; D-014 pasa a definitiva.

**Estado:** [ ] pendiente.

---

## Fase 6 — Franjas horarias y estadística descriptiva

**Objetivo:** describir los datos (distribuciones, perfil diurno, franjas) y confirmar o corregir las hipótesis de las franjas.

**Entregables:**
- [ ] Perfil diurno de cada variable, calculado **solo con datos de entrenamiento** (las fechas del split se fijan aquí de forma preliminar).
- [ ] Cálculo de franjas con la regla de mínimo de horas y NaN.
- [ ] Decisión sobre el tratamiento de PM2.5 en las franjas (DP-01).
- [ ] Tablas descriptivas por variable y por franja.

**Conceptos que se estudiarán:**
- *Perfil diurno*: identificar el ciclo típico del día.
- *Estadísticos robustos (mediana, percentiles)*: describir datos asimétricos como PM2.5.
- *Agrupación por día civil local*: evitar asignar la franja de la noche al día UTC siguiente.
- *Tratamiento de NaN*: no ocultar la falta de datos.

**Criterio de verificación:** para un día elegido a mano, el estudiante calcula las 3 franjas con lápiz y papel y coinciden con las del programa, incluido un caso con NaN y la franja de la noche.

**Dependencias:** Fase 5.

**Decisiones abiertas:** DP-01; D-009 pasa a definitiva o se corrige.

**Estado:** [ ] pendiente.

---

## Fase 7 — Regresión lineal y evaluación

**Objetivo:** entrenar y evaluar la regresión según [regresion.md](regresion.md), compararla con la línea base e interpretar los resultados con prudencia.

**Entregables:**
- [ ] Conjunto unido de PM2.5 y predictoras, con la resolución decidida (DP-02).
- [ ] Split temporal con hueco de 24 h y las fechas exactas documentadas.
- [ ] Pipeline (escalador + regresión) ajustado solo con el entrenamiento.
- [ ] Tabla de métricas (MAE, RMSE, R²) del modelo y de la línea base.
- [ ] Diagnósticos: VIF, autocorrelación de residuos y distribución de PM2.5 (DP-08).
- [ ] Un párrafo de interpretación con la formulación prudente recomendada.

**Conceptos que se estudiarán:**
- *Mínimos cuadrados*: cómo se obtienen los coeficientes.
- *Fuga de información*: por qué el Pipeline y el split temporal.
- *MAE, RMSE y R²*: qué mide cada métrica.
- *Línea base*: el mínimo que debe superar un modelo.
- *VIF y autocorrelación*: cuándo no confiar en los coeficientes o en los p-valores.
- *Correlación frente a causalidad*: límites de la interpretación.

**Criterio de verificación:** las métricas son reproducibles (la misma ejecución da el mismo resultado), el modelo se compara explícitamente con la línea base y el estudiante responde las 4 [preguntas de comprobación](regresion.md#preguntas-de-comprobación).

**Dependencias:** Fase 6.

**Decisiones abiertas:** DP-02, DP-08; las proporciones de D-018.

**Estado:** [ ] pendiente.

---

## Fase 8 — Visualizaciones

**Objetivo:** producir las gráficas de [cli-y-visualizaciones.md](cli-y-visualizaciones.md#gráficas-previstas) con salida en ventana o PNG.

**Entregables:**
- [ ] Series temporales, perfil diurno, comparación por franjas, dispersiones, matriz de correlación, real frente a predicho, residuos y mapa de cobertura.
- [ ] Salida en ventana y en PNG en `outputs/`, con atribución de la fuente en cada gráfica.
- [ ] Comportamiento sin entorno gráfico (PV-18).

**Conceptos que se estudiarán:**
- *Elección del tipo de gráfica según la pregunta*: cada gráfica responde algo concreto.
- *Representación honesta de los huecos*: no unir puntos donde faltan datos.
- *Backends de Matplotlib*: ventana interactiva frente a archivo.

**Criterio de verificación:** cada gráfica tiene título, unidades, periodo y fuente, y se puede explicar qué pregunta responde. El mapa de cobertura coincide con el informe de cobertura de la opción 1.

**Dependencias:** Fases 6 y 7.

**Decisiones abiertas:** DP-10.

**Estado:** [ ] pendiente.

---

## Fase 9 — CLI integrada, pruebas finales, documentación final y defensa oral

**Objetivo:** integrar todo en el menú de 7 opciones, probar el flujo completo desde una base vacía, actualizar la documentación con lo aprendido y preparar la defensa.

**Entregables:**
- [ ] Menú completo según [cli-y-visualizaciones.md](cli-y-visualizaciones.md).
- [ ] Prueba completa: base vacía → cobertura → actualización → consulta → estadísticas → regresión → gráficas.
- [ ] Documentación actualizada: todas las [Por verificar] resueltas o justificadas, y decisiones en estado final.
- [ ] Instrucciones de instalación y ejecución en el README.
- [ ] Guion de la defensa oral: arquitectura, flujo de datos, decisiones clave y limitaciones.

**Conceptos que se estudiarán:**
- *Pruebas de extremo a extremo*: validar el sistema completo, no solo sus partes.
- *Comunicación de limitaciones*: presentar resultados sin sobrevenderlos.

**Criterio de verificación:** una persona ajena puede instalar y ejecutar el proyecto siguiendo el README, y el estudiante puede responder sin notas: ¿por qué Java y Python?, ¿por qué JSON Lines?, ¿por qué ERA5 explícito?, ¿por qué PM2.5 no es una medición?, ¿por qué un split temporal?, ¿qué significa el R² obtenido?

**Dependencias:** Fases 1–8.

**Decisiones abiertas:** ninguna nueva; se cierran las restantes.

**Estado:** [ ] pendiente.

---

## Decisiones pendientes

| ID | Decisión | Relacionada con | Opciones / propuesta | Se resuelve en | ¿Requiere opinión del estudiante? |
|---|---|---|---|---|---|
| DP-01 | Tratamiento de PM2.5 en las franjas (paso de 3 h) | D-006, D-009 | (1) un valor nativo por franja [recomendada]; (2) desplazar las ventanas; (3) aceptar valores interpolados | Fase 6 (con datos de la Fase 1) | Sí |
| DP-02 | Resolución de PM2.5 en la regresión | D-006, D-017 | Solo los pasos nativos [recomendada] o todas las horas devueltas | Fase 7 (con datos de la Fase 1) | Sí |
| DP-03 | Umbral de cobertura de PM2.5 según su paso | D-014 | Pasos esperados de 3 h para PM2.5 [recomendada] | Fase 5 | No |
| DP-04 | Mecanismo del lote de corrección | D-013 | Sobrescribir el valor y apuntar al lote nuevo, guardando el valor anterior en el lote; o no implementar correcciones en este proyecto | Fase 2 | Sí |
| DP-05 | Tabla definitiva de códigos de salida | D-003, D-004 | Propuesta 0–4 de [arquitectura.md](arquitectura.md#códigos-de-salida-propuesta) | Fase 4 | No |
| DP-06 | Unidad canónica del viento | D-022 | m/s [recomendada] o km/h | Fase 3 | No |
| DP-07 | Versión de Java y variante de ObjectDB | D-002 | `javax` (Java ≥ 8) o `jakarta` (Java ≥ 17) | Fase 2 | Sí (depende de lo instalado y de lo que use la asignatura) |
| DP-08 | Transformación logarítmica de PM2.5 | D-017 | Escala original [recomendada] o log | Fase 7 | Sí |
| DP-09 | Regla del 29 de febrero | D-016 | Usar el 28 de febrero del año anterior [recomendada] | Fase 5 | No |
| DP-10 | Salida de las gráficas por defecto | D-023 | Preguntar cada vez; PNG si no hay pantalla | Fase 8 | Sí |
| DP-11 | Coordenadas y elevación del punto | D-007 | Un punto del centro de Medellín, con elevación fija o automática | Fase 1 | Sí |
| DP-12 | Volver a pedir registros existentes con todo a null | D-015 | No volver a pedirlos automáticamente [recomendada] | Fase 5 | No |

## Puntos por verificar

| ID | Punto | Documento de origen | Se verifica en |
|---|---|---|---|
| PV-01 | Coordenadas del punto representativo del centro de Medellín | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-02 | Elevación que se fijará y su efecto en el reescalado | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-03 | Nombre y valor exactos del parámetro para seleccionar ERA5 | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-04 | Corte real de la latencia de ERA5 (¿día D−5 completo?) | [cobertura-y-franjas.md](cobertura-y-franjas.md) | Fase 1 |
| PV-05 | **Paso real de PM2.5 en la respuesta (horario interpolado o cada 3 h con null)** | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-06 | Un año completo de PM2.5 y de ERA5 disponible para Medellín | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-07 | Revisiones de ERA5 reciente y cambios de versión de CAMS dentro del año | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-08 | Convención del timestamp (instantáneo o agregado de la hora anterior) | [cobertura-y-franjas.md](cobertura-y-franjas.md) | Fase 1 |
| PV-09 | Representación de los ausentes en las respuestas (`null`) | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-10 | Rango máximo de fechas por petición | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-11 | Texto de atribución exigido para CAMS global | [fuentes-y-datos.md](fuentes-y-datos.md) | Fase 1 |
| PV-12 | Si CAMS usa meteorología del ECMWF (IFS) como entrada | [regresion.md](regresion.md) | Fase 1 |
| PV-13 | Índice único compuesto que incluya una relación con Location | [arquitectura.md](arquitectura.md) | Fase 2 |
| PV-14 | Tipo temporal de Java admitido por ObjectDB para timestamps UTC | [arquitectura.md](arquitectura.md) | Fase 2 |
| PV-15 | Comportamiento del archivo `.odb` con dos procesos simultáneos | [arquitectura.md](arquitectura.md) | Fase 4 |
| PV-16 | America/Bogota = UTC−5 sin horario de verano en la base tz | [cobertura-y-franjas.md](cobertura-y-franjas.md) | Fase 3 |
| PV-17 | Versiones de Python, Pandas, scikit-learn y Matplotlib | [README.md](../README.md) | Fase 3 |
| PV-18 | Comportamiento de Matplotlib sin entorno gráfico | [cli-y-visualizaciones.md](cli-y-visualizaciones.md) | Fase 8 |
| PV-19 | Formato de `coverage` (lista de timestamps o intervalos) y argumentos de los subcomandos | [arquitectura.md](arquitectura.md) | Fase 4 |

## Limitaciones y supuestos

- El orden de las fases supone que la Fase 1 no invalida la fuente de PM2.5. Si lo hiciera (por ejemplo, si no hubiera un año completo para Medellín), habría que replantear D-006 antes de la Fase 3.
- Las fases no tienen fechas asignadas; el calendario depende de la asignatura.
- Las casillas de los entregables de la Fase 0 reflejan la creación de los documentos, no su aprobación por el estudiante ni por el profesor.
- Los identificadores DP-xx y PV-xx son propios de este documento; los demás documentos los citan cuando corresponde.
