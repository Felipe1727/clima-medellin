# Spec Delta

## Purpose

Define el contrato de línea de comandos del JAR de persistencia que Python invoca como proceso hijo: qué escribe en stdout y stderr y con qué código termina.

## ADDED Requirements

### Requirement: Salida JSON única por stdout
El JAR SHALL escribir en stdout exactamente un objeto JSON por ejecución, y nada más. Los mensajes de registro SHALL ir a stderr.

#### Scenario: Cualquier ejecución deja un único JSON en stdout
- **WHEN** se ejecuta el JAR con cualquier combinación de argumentos
- **THEN** stdout contiene exactamente un objeto JSON válido en una sola línea

### Requirement: Error de uso sin subcomando o con subcomando desconocido
Cuando no se indica subcomando o el subcomando no existe, el JAR SHALL responder con un objeto JSON de error con `ok` a `false`, un `error.type` igual a `USAGE` y un `error.message` en español, y SHALL terminar con código de salida 1.

#### Scenario: Ejecución sin argumentos
- **WHEN** se ejecuta `java -jar clima-medellin.jar` sin argumentos
- **THEN** stdout contiene `{"ok":false,"error":{"type":"USAGE","message":...}}` y el código de salida es 1

#### Scenario: Subcomando desconocido
- **WHEN** se ejecuta `java -jar clima-medellin.jar foo`
- **THEN** stdout contiene un objeto JSON con `ok` a `false` y `error.type` igual a `USAGE`, el mensaje menciona `foo` y el código de salida es 1
