# Spec Delta

## ADDED Requirements

### Requirement: Arranque de la aplicación
Al instalar el proyecto Python, SHALL quedar disponible el comando `clima-medellin`. Sin opciones SHALL abrir el menú interactivo; con `--verbose` SHALL abrir el menú mostrando además los registros del JAR; con `--version` SHALL imprimir la versión.

#### Scenario: Consulta de la versión
- **WHEN** se ejecuta `clima-medellin --version` tras `uv sync`
- **THEN** se imprime `clima-medellin <versión>` y el código de salida es 0

#### Scenario: Ejecución sin opciones
- **WHEN** se ejecuta `clima-medellin` sin opciones y el usuario elige la opción 7
- **THEN** se muestra el menú, después un mensaje de despedida, y el código de salida es 0

#### Scenario: Modo detallado
- **WHEN** se ejecuta `clima-medellin --verbose`
- **THEN** el menú usa el puente con el modo detallado activado

## REMOVED Requirements

### Requirement: Comando instalado por el proyecto
**Reason**: describía el comportamiento provisional previo al menú (imprimir que el menú no estaba disponible).
**Migration**: sustituido por «Arranque de la aplicación», que conserva `--version` y abre el menú sin opciones.
