# charts Specification

## Purpose
Genera las gráficas que ayudan a entender los datos y el modelo (series, perfil diurno, franjas, relaciones, resultados de la regresión, cobertura y empalmes), siempre anotadas con su periodo y su fuente, y las muestra en una ventana o las guarda como PNG.

## Requirements

### Requirement: Anotación obligatoria
Cada gráfica SHALL tener un título, ejes rotulados con su unidad (o con «hora local», «fecha» u otra magnitud sin unidad cuando corresponda), el periodo representado y la nota «Datos: Open-Meteo.com (ERA5, CAMS)».

#### Scenario: Gráfica cualquiera
- **WHEN** se genera cualquiera de las gráficas
- **THEN** la figura tiene título, el texto del periodo y la nota de atribución, y sus ejes de magnitudes físicas incluyen la unidad entre paréntesis

### Requirement: Gráficas de los datos
El sistema SHALL generar series temporales por variable, el perfil diurno del entrenamiento con banda de dispersión y franjas sombreadas, diagramas de caja por franja con los días válidos, la dispersión de PM2.5 frente a cada predictora, la matriz de correlación de las cuatro variables, un mapa de cobertura días × horas locales por fuente y el salto absoluto medio de PM2.5 por hora UTC con las 00 y 12 UTC destacadas.

#### Scenario: Diagnóstico de empalmes
- **WHEN** se genera la gráfica de empalmes con un año de PM2.5
- **THEN** tiene 24 barras, una por hora UTC, y las de las 00 y 12 UTC están destacadas y rotuladas

### Requirement: Gráficas del modelo
El sistema SHALL generar, a partir de una regresión entrenada, la gráfica de real frente a predicho (dispersión con la recta y = x y serie temporal superpuesta) y la de residuos (frente a predichos, en el tiempo e histograma).

#### Scenario: Gráficas de la regresión
- **WHEN** se generan las gráficas de resultados a partir de una regresión entrenada
- **THEN** se obtienen la de real frente a predicho y la de residuos con datos solo del periodo de prueba

### Requirement: Huecos sin unir
Las series temporales SHALL mostrar las horas sin dato como cortes de la línea, sin unir los puntos de un lado y otro del hueco.

#### Scenario: Serie con un hueco
- **WHEN** a una serie le faltan 5 horas seguidas
- **THEN** la línea dibujada tiene valores nulos en esas horas y no hay un segmento que una sus extremos

### Requirement: Salida en ventana o PNG
Cada gráfica SHALL poder mostrarse en una ventana o guardarse como PNG en `outputs/` con el nombre `<gráfica>_<AAAAmmdd-HHMMSS>.png`, sin sobrescribir un archivo existente. Si se pide la ventana y no hay pantalla disponible, SHALL guardarse el PNG y SHALL devolverse un aviso en español.

#### Scenario: Guardar como PNG
- **WHEN** se guarda la gráfica `perfil_diurno` como PNG
- **THEN** existe un archivo `outputs/perfil_diurno_<AAAAmmdd-HHMMSS>.png`

#### Scenario: Sin pantalla
- **WHEN** se pide mostrar una gráfica en una ventana y no hay entorno gráfico
- **THEN** se guarda el PNG y se devuelve un aviso que indica la ruta
