"""Presentación en la terminal con rich: tablas, paneles, colores y textos en lenguaje sencillo."""

import math

import pandas as pd
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# El color acompaña siempre a una palabra: la información nunca depende solo del color (D-025).
STATE_STYLE = {"COMPLETA": "green", "PARCIAL": "yellow", "SIN_DATOS": "red"}
STATE_WORD = {"COMPLETA": "completa", "PARCIAL": "incompleta", "SIN_DATOS": "sin datos"}

# Términos técnicos con su traducción, tal como aparecen en las tablas.
TERMS = {
    "MAE": "error típico (MAE)",
    "RMSE": "error con más peso en los picos (RMSE)",
    "R2": "qué tanto explica el modelo (R²)",
    "VIF": "redundancia con otras variables (VIF)",
    "DW": "dependencia entre horas seguidas (Durbin-Watson)",
    "modelo": "modelo",
    "linea_base": "línea base (predecir siempre la media)",
    "estandarizado": "efecto por desviación típica",
    "original": "efecto por unidad",
    "n": "datos",
    "nulos": "sin valor",
    "media": "media",
    "mediana": "mediana",
    "desv": "desviación típica",
    "min": "mínimo",
    "max": "máximo",
    "p5": "percentil 5",
    "p25": "percentil 25",
    "p75": "percentil 75",
    "p95": "percentil 95",
    "dias_validos": "días con dato",
}


def make_console() -> Console:
    """Consola de la aplicación; rich respeta NO_COLOR y no colorea si no es una terminal."""
    return Console(highlight=False)


def format_value(value, decimals: int = 2) -> str:
    """Número con los decimales indicados; «—» para un valor ausente."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


def df_table(
    frame: pd.DataFrame, title: str | None = None, *, index_name: str = "", decimals: int = 2
) -> Table:
    """Tabla de rich a partir de un DataFrame, con los nombres de columna traducidos."""
    table = Table(title=title, box=box.SIMPLE_HEAVY, title_justify="left", header_style="bold cyan")
    show_index = index_name != "" or not isinstance(frame.index, pd.RangeIndex)
    if show_index:
        table.add_column(index_name or "", style="bold")
    for column in frame.columns:
        name = " ".join(map(str, column)) if isinstance(column, tuple) else str(column)
        table.add_column(TERMS.get(name, name), justify="right")
    for label, row in frame.iterrows():
        cells = [format_value(v, decimals) for v in row]
        if show_index:
            label = " · ".join(map(str, label)) if isinstance(label, tuple) else str(label)
            cells = [TERMS.get(label, label)] + cells
        table.add_row(*cells)
    return table


def meaning(text: str) -> Panel:
    """Panel final de cada pantalla: qué significan los resultados, en palabras sencillas."""
    return Panel(
        text, title="Qué significa", title_align="left", border_style="blue", padding=(0, 1)
    )


def state_text(state: str) -> Text:
    """Estado de una fuente en color y con palabra."""
    return Text(f"{state} ({STATE_WORD[state]})", style=STATE_STYLE[state])


def ok(text: str) -> Text:
    return Text.assemble(("[OK] ", "bold green"), text)


def progress_line(text: str) -> Text:
    return Text.assemble(("[…] ", "bold cyan"), text)


def warn(text: str) -> Text:
    return Text.assemble(("[AVISO] ", "bold yellow"), text)


def error(text: str) -> Text:
    return Text.assemble(("[ERROR] ", "bold red"), text)
