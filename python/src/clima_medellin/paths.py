"""Rutas del proyecto, relativas a la raíz del repositorio."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "clima.odb"
STAGING_DIR = ROOT / "staging"
EXCHANGE_DIR = ROOT / "exchange"
OUTPUTS_DIR = ROOT / "outputs"
JAR_PATH = ROOT / "java" / "target" / "clima-medellin.jar"
