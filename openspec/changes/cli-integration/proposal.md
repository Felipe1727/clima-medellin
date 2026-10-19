# Proposal

## Why

Todas las piezas existen (descarga, persistencia, cobertura, análisis, regresión y gráficas), pero el comando `clima-medellin` todavía no las ofrece: solo imprime que el menú no está disponible. La Fase 9 las integra en el menú de 7 opciones de [cli-y-visualizaciones.md](../../../docs/cli-y-visualizaciones.md), prueba el flujo completo desde una base vacía y deja la documentación en su estado final.

## What Changes

- Menú interactivo de 7 opciones con cabecera (ubicación y ventana) y mensajes `[OK]`, `[…]`, `[AVISO]` y `[ERROR]`:
  1. verificar cobertura (tabla por fuente y variable, intervalos faltantes más grandes);
  2. actualizar datos (plan, llamadas estimadas, confirmación `[s/N]`, progreso por intervalo, resumen de cada lote y cobertura resultante);
  3. consultar registros (rango de fechas locales y fuente; tabla paginada con hora local y UTC, `—` para nulos y lote de origen);
  4. estadísticas descriptivas (por variable y por franja);
  5. entrenar y evaluar la regresión (fechas, tamaños, métricas frente a la línea base, coeficientes, VIF, Durbin-Watson);
  6. generar visualizaciones (ventana o PNG);
  7. salir.
- Reglas comunes: las opciones 3 a 6 avisan si la cobertura no es `COMPLETA` y preguntan si continuar; con la base vacía sugieren la opción 2. Los errores del puente y de la API se muestran en español sin cerrar el programa.
- Opción `--verbose` para ver los registros de Java.
- El menú es una capa fina sobre funciones existentes, con entrada y salida inyectables para probarlo con entradas programadas.
- Prueba de extremo a extremo con una base temporal y la API falsa de las muestras.
- README con instrucciones de instalación y ejecución; `docs/fases.md` con todas las fases actualizadas; revisión final de `docs/implementacion.md` (sección 9 e índice completo).

## Capabilities

### New Capabilities
- `interactive-menu`: menú de terminal de 7 opciones que da acceso a cobertura, actualización, consulta, estadísticas, regresión y gráficas.

### Modified Capabilities
- `app-cli`: el requisito provisional «Comando instalado por el proyecto» se sustituye por «Arranque de la aplicación»: sin opciones abre el menú y se añade `--verbose`.

## Impact

- Código: `python/src/clima_medellin/cli.py` (reescrito) y `menu.py` (nuevo), con pruebas.
- Documentación: `README.md`, `docs/implementacion.md`, `docs/fases.md`, `docs/cli-y-visualizaciones.md`, `docs/arquitectura.md`.
