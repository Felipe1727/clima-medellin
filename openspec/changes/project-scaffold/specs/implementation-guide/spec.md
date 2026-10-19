# Spec Delta

## Purpose

Garantiza que el proyecto tiene una guía técnica en español, `docs/implementacion.md`, cuyos fragmentos de código reales coinciden siempre con el código del repositorio.

## ADDED Requirements

### Requirement: Estructura de la guía técnica
El documento `docs/implementacion.md` SHALL existir e incluir su propósito, un índice, la convención de fragmentos y las instrucciones para compilar y ejecutar el proyecto. Cada tema SHALL seguir el formato Concepto, Sintaxis básica, En este proyecto y Cuidado.

#### Scenario: Guía presente
- **WHEN** se abre `docs/implementacion.md`
- **THEN** contiene las secciones de propósito, índice, convención de fragmentos y compilación y ejecución

### Requirement: Marcado de fragmentos reales
Cada fragmento de código real SHALL ser un bloque de código delimitado precedido inmediatamente por un comentario `<!-- fragmento: <ruta relativa al repositorio> -->`, y SHALL ser código literal y contiguo, sin omisiones.

#### Scenario: Fragmento marcado
- **WHEN** la guía muestra código tomado del proyecto
- **THEN** el bloque va precedido por `<!-- fragmento: ... -->` con la ruta del archivo de origen

### Requirement: Verificación automática de fragmentos
La batería de pruebas SHALL fallar si algún fragmento marcado no aparece literalmente en su archivo de origen (ignorando los espacios finales de cada línea), si el archivo no existe o si la guía no contiene ningún fragmento marcado.

#### Scenario: Fragmento vigente
- **WHEN** todos los fragmentos marcados aparecen literalmente en sus archivos
- **THEN** la prueba de fragmentos pasa

#### Scenario: Fragmento desactualizado
- **WHEN** el código de origen cambia y un fragmento marcado deja de coincidir
- **THEN** la prueba de fragmentos falla indicando la ruta del fragmento que no coincide

#### Scenario: Archivo de origen inexistente
- **WHEN** un fragmento marcado cita una ruta que no existe
- **THEN** la prueba de fragmentos falla indicando esa ruta
