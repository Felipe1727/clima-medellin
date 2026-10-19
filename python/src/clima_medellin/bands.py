"""Franjas horarias y perfil diurno en hora de Medellín (D-009, D-021)."""

import pandas as pd

from clima_medellin.config import LOCAL_TZ
from clima_medellin.split import Split

# Horas locales de cada franja (ventanas de 3 horas centradas en 8, 14 y 20 h).
BANDS = {"mañana": (7, 8, 9), "tarde": (13, 14, 15), "noche": (19, 20, 21)}
MIN_VALID_HOURS = 2


def to_local(frame: pd.DataFrame) -> pd.DataFrame:
    """Convierte el índice UTC a America/Bogota (por nombre de zona, no con un -5 fijo)."""
    return frame.tz_convert(LOCAL_TZ)


def daily_bands(frame: pd.DataFrame) -> pd.DataFrame:
    """Valor de cada franja por día civil local y variable.

    Promedio de los valores no nulos de las 3 horas; NaN si hay menos de 2 (no se
    interpola). Columnas: MultiIndex (variable, franja). Índice: fecha local.
    """
    local = to_local(frame)
    pieces = {}
    for band, hours in BANDS.items():
        in_band = local[local.index.hour.isin(hours)]
        # Se agrupa por el día civil local, no por el día UTC: la noche (19-21 h) cae
        # en el día UTC siguiente (00-02 UTC).
        grouped = in_band.groupby(in_band.index.date)
        mean, count = grouped.mean(), grouped.count()
        pieces[band] = mean.where(count >= MIN_VALID_HOURS)
    result = pd.concat(pieces, axis=1).swaplevel(axis=1)
    columns = pd.MultiIndex.from_product([frame.columns, list(BANDS)])
    result = result.reindex(columns=columns)
    result.index.name = "fecha_local"
    return result


def diurnal_profile(frame: pd.DataFrame, split: Split) -> pd.DataFrame:
    """Media y número de valores válidos por hora local (0-23), solo con el entrenamiento."""
    local = to_local(split.train(frame))
    grouped = local.groupby(local.index.hour)
    profile = pd.concat({"media": grouped.mean(), "n": grouped.count()}, axis=1).swaplevel(axis=1)
    columns = pd.MultiIndex.from_product([frame.columns, ["media", "n"]])
    profile = profile.reindex(index=range(24), columns=columns)
    for column in frame.columns:
        profile[(column, "n")] = profile[(column, "n")].fillna(0).astype(int)
    profile.index.name = "hora_local"
    return profile
