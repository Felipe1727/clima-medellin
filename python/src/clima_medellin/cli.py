"""Comando de terminal ``clima-medellin``: abre el menú de 7 opciones."""

import argparse

from clima_medellin import __version__
from clima_medellin.bridge import JavaBridge
from clima_medellin.menu import Menu


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del comando; devuelve el código de salida."""
    parser = argparse.ArgumentParser(
        prog="clima-medellin",
        description="Clima y PM2.5 de Medellín: cobertura, actualización y análisis.",
    )
    parser.add_argument("--version", action="version", version=f"clima-medellin {__version__}")
    parser.add_argument(
        "--verbose", action="store_true", help="muestra los mensajes de registro del JAR de Java"
    )
    args = parser.parse_args(argv)
    Menu(JavaBridge(verbose=args.verbose)).run()
    return 0
