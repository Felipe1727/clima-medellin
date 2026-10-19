"""Estadísticas descriptivas por variable y por franja."""

import pandas as pd

PERCENTILES = {"p5": 0.05, "p25": 0.25, "p75": 0.75, "p95": 0.95}


def describe_variables(frame: pd.DataFrame) -> pd.DataFrame:
    """Una fila por variable: n, nulos, media, mediana, desviación, extremos y percentiles.

    ``nulos`` cuenta los valores nulos de las filas presentes; las horas sin ningún
    registro las informa la cobertura.
    """
    rows = {}
    for column in frame.columns:
        values = frame[column]
        valid = values.dropna()
        row = {
            "n": int(valid.size),
            "nulos": int(values.isna().sum()),
            "media": valid.mean(),
            "mediana": valid.median(),
            "desv": valid.std(),
            "min": valid.min(),
            "max": valid.max(),
        }
        for name, q in PERCENTILES.items():
            row[name] = valid.quantile(q)
        rows[column] = row
    return pd.DataFrame.from_dict(rows, orient="index")


def describe_bands(bands: pd.DataFrame) -> pd.DataFrame:
    """Una fila por (variable, franja): media de las franjas válidas y días válidos."""
    result = pd.DataFrame({"media": bands.mean(), "dias_validos": bands.count()})
    result.index.names = ["variable", "franja"]
    return result
