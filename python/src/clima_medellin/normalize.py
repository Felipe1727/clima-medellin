"""Conversión de una respuesta de Open-Meteo en una tabla horaria limpia y validada."""

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from clima_medellin.config import SOURCES

# Open-Meteo escribe «μ» (letra griega mu); se acepta también «µ» (signo micro).
_UNIT_ALIASES = {"μg/m³": "µg/m³"}


class NormalizationError(Exception):
    """La respuesta no tiene el formato o las unidades esperadas."""


@dataclass
class NormalizationReport:
    """Qué se hizo con cada fila y valor de la respuesta."""

    received: int = 0
    duplicates: int = 0
    after_effective_end: int = 0
    all_null: int = 0
    out_of_range: dict[str, int] = field(default_factory=dict)
    rows: int = 0


@dataclass
class Normalized:
    frame: pd.DataFrame
    report: NormalizationReport


def normalize(source: str, payload: dict, effective_end: datetime) -> Normalized:
    """Convierte el JSON de una fuente en un DataFrame indexado por timestamp UTC.

    ``effective_end`` es el primer instante UTC que ya no se guarda (exclusivo).
    """
    config = SOURCES[source]
    hourly = payload["hourly"]
    units = payload.get("hourly_units", {})
    for variable in config.variables:
        unit = _UNIT_ALIASES.get(units.get(variable.api_name), units.get(variable.api_name))
        if unit != variable.unit:
            raise NormalizationError(
                f"{source}: {variable.api_name} llega en {units.get(variable.api_name)!r}, "
                f"se esperaba {variable.unit!r}"
            )

    # Las horas llegan en GMT sin sufijo de zona: se interpretan explícitamente como UTC.
    index = pd.DatetimeIndex(pd.to_datetime(hourly["time"], utc=True), name="timestamp_utc")
    frame = pd.DataFrame(
        {
            v.column: pd.to_numeric(pd.Series(hourly[v.api_name]), errors="coerce").to_numpy(float)
            for v in config.variables
        },
        index=index,
    )
    report = NormalizationReport(received=len(frame))

    # Valores imposibles: pasan a NaN (nunca a 0) y se cuentan por variable.
    for variable in config.variables:
        column = frame[variable.column]
        plausible = column.isna() | column.between(variable.minimum, variable.maximum)
        report.out_of_range[variable.column] = int((~plausible).sum())
        frame[variable.column] = column.where(plausible)

    duplicated = frame.index.duplicated(keep="first")
    report.duplicates = int(duplicated.sum())
    frame = frame[~duplicated]

    end = pd.Timestamp(effective_end)
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
    late = frame.index >= end
    report.after_effective_end = int(late.sum())
    frame = frame[~late]

    empty = frame.isna().all(axis=1)
    report.all_null = int(empty.sum())
    frame = frame[~empty].sort_index()

    report.rows = len(frame)
    return Normalized(frame=frame, report=report)
