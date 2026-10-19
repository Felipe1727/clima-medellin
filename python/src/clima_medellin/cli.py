"""Comando de terminal ``clima-medellin``."""

import argparse

from clima_medellin import __version__


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del comando; devuelve el código de salida."""
    parser = argparse.ArgumentParser(
        prog="clima-medellin",
        description="Clima y PM2.5 de Medellín: cobertura, actualización y análisis.",
    )
    parser.add_argument("--version", action="version", version=f"clima-medellin {__version__}")
    parser.parse_args(argv)
    # El menú de 7 opciones llega en la especificación cli-integration.
    print("El menú de Clima Medellín aún no está disponible.")
    return 0
