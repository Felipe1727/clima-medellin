"""Configuración común de las pruebas: Matplotlib sin ventanas (backend Agg)."""

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
