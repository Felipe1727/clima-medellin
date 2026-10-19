"""Tabla de análisis: ERA5 y CAMS global unidos por timestamp UTC."""

import pandas as pd

from clima_medellin.bridge import JavaBridge
from clima_medellin.config import CAMS_GLOBAL, ERA5
from clima_medellin.coverage import Window

COLUMNS = ERA5.columns + CAMS_GLOBAL.columns


def combine(weather: pd.DataFrame, air: pd.DataFrame) -> pd.DataFrame:
    """Une las dos fuentes conservando las horas que solo tiene una de ellas."""
    joined = weather[ERA5.columns].join(air[CAMS_GLOBAL.columns], how="outer")
    return joined.sort_index()[COLUMNS]


def load_window(bridge: JavaBridge, win: Window) -> pd.DataFrame:
    """Exporta de la base las dos fuentes dentro de la ventana y las combina."""
    weather = bridge.export("ERA5", win.start_utc, win.end_utc)
    air = bridge.export("CAMS_GLOBAL", win.start_utc, win.end_utc)
    return combine(weather, air)
