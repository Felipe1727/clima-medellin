# app-cli Specification

## Purpose
Define el comando de terminal `clima-medellin` con el que el usuario arranca la aplicación Python; esta especificación fija su instalación y su versión, y las siguientes añadirán el menú.

## Requirements

### Requirement: Comando instalado por el proyecto
Al instalar el proyecto Python, SHALL quedar disponible el comando `clima-medellin`.

#### Scenario: Consulta de la versión
- **WHEN** se ejecuta `clima-medellin --version` tras `uv sync`
- **THEN** se imprime `clima-medellin <versión>` y el código de salida es 0

#### Scenario: Ejecución sin opciones antes de implementar el menú
- **WHEN** se ejecuta `clima-medellin` sin opciones
- **THEN** se imprime un mensaje en español que indica que el menú aún no está disponible y el código de salida es 0
