"""Ventana móvil, fin efectivo por fuente y medición de la cobertura (funciones puras)."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

import pandas as pd

from clima_medellin.config import LOCAL_TZ, SOURCES

# Umbrales de D-014: decisiones de diseño, no estándares meteorológicos.
MIN_COVERAGE_PCT = 98.0
MAX_GAP_HOURS = 6
# ERA5 publica con 5 días de retraso: el día D-5 es el último completo (PV-04).
ERA5_LAST_FULL_DAY_OFFSET = 5

STEP = pd.Timedelta(hours=1)


@dataclass(frozen=True)
class Window:
    start_local: date
    end_local: date
    start_utc: datetime
    end_utc: datetime

    @property
    def days(self) -> int:
        return (self.end_local - self.start_local).days


def today_local() -> date:
    """Fecha de hoy en Medellín (no en UTC: a las 21:00 locales ya es mañana en UTC)."""
    return datetime.now(LOCAL_TZ).date()


def one_year_before(day: date) -> date:
    """Mismo día del año anterior; el 29 de febrero pasa al 28 de febrero (DP-09)."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def _local_midnight_utc(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=LOCAL_TZ).astimezone(UTC)


def window(today: date) -> Window:
    """Ventana [mismo día del año anterior, hoy) a las 00:00 locales, con extremos en UTC."""
    start = one_year_before(today)
    return Window(start, today, _local_midnight_utc(start), _local_midnight_utc(today))


def effective_end(source: str, win: Window, today: date) -> datetime:
    """Primer instante UTC que ya no se espera ni se guarda para la fuente (exclusivo)."""
    if source == "ERA5":
        first_unpublished_day = today - timedelta(days=ERA5_LAST_FULL_DAY_OFFSET - 1)
        published_until = datetime.combine(first_unpublished_day, time.min, tzinfo=UTC)
        return min(win.end_utc, published_until)
    return win.end_utc


def expected_steps(start: datetime, end: datetime) -> pd.DatetimeIndex:
    """Todas las horas en punto de [start, end) en UTC."""
    first = pd.Timestamp(start).tz_convert("UTC").ceil("h")
    return pd.date_range(first, pd.Timestamp(end).tz_convert("UTC"), freq="h", inclusive="left")


def missing_steps(expected: pd.DatetimeIndex, existing: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Pasos esperados que no están entre los existentes."""
    return expected.difference(existing)


def group_intervals(steps: pd.DatetimeIndex) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Agrupa horas consecutivas en intervalos (primera hora, última hora)."""
    intervals: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for ts in steps.sort_values():
        if intervals and ts - intervals[-1][1] == STEP:
            intervals[-1] = (intervals[-1][0], ts)
        else:
            intervals.append((ts, ts))
    return intervals


def to_request_dates(
    intervals: list[tuple[pd.Timestamp, pd.Timestamp]],
) -> list[tuple[date, date]]:
    """Convierte intervalos horarios en rangos de fechas UTC (la API pide días completos).

    Los rangos que se tocan o se solapan una vez convertidos a días se fusionan.
    """
    requests: list[tuple[date, date]] = []
    for first, last in intervals:
        start, end = first.date(), last.date()
        if requests and start <= requests[-1][1] + timedelta(days=1):
            requests[-1] = (requests[-1][0], max(requests[-1][1], end))
        else:
            requests.append((start, end))
    return requests


@dataclass(frozen=True)
class VariableCoverage:
    column: str
    expected: int
    valid: int
    percent: float
    max_gap_hours: int
    gaps: int


def variable_coverage(
    column: str, expected: pd.DatetimeIndex, valid: pd.DatetimeIndex
) -> VariableCoverage:
    """Métricas de una variable: válidos frente a esperados y huecos."""
    valid_in_window = expected.intersection(valid)
    gaps = group_intervals(missing_steps(expected, valid_in_window))
    longest = max((int((last - first) / STEP) + 1 for first, last in gaps), default=0)
    percent = 100.0 * len(valid_in_window) / len(expected) if len(expected) else 0.0
    return VariableCoverage(
        column, len(expected), len(valid_in_window), percent, longest, len(gaps)
    )


@dataclass(frozen=True)
class CoverageReport:
    source: str
    start_utc: datetime
    effective_end: datetime
    records_in_window: int
    variables: list[VariableCoverage]
    state: str
    missing: pd.DatetimeIndex


def state_of(records_in_window: int, variables: list[VariableCoverage]) -> str:
    """COMPLETA, PARCIAL o SIN_DATOS según D-014."""
    if records_in_window == 0:
        return "SIN_DATOS"
    if all(v.percent >= MIN_COVERAGE_PCT and v.max_gap_hours <= MAX_GAP_HOURS for v in variables):
        return "COMPLETA"
    return "PARCIAL"


def coverage_report(
    source: str, existing: pd.DataFrame, win: Window, today: date
) -> CoverageReport:
    """Cobertura de una fuente a partir de lo guardado.

    ``existing`` está indexado por timestamp UTC y tiene una columna booleana por variable
    (True si el valor no es nulo), tal como lo devuelve ``JavaBridge.coverage``.
    """
    end = effective_end(source, win, today)
    expected = expected_steps(win.start_utc, end)
    in_window = existing.index.intersection(expected)
    variables = [
        variable_coverage(column, expected, existing.index[existing[column].to_numpy(bool)])
        for column in SOURCES[source].columns
    ]
    return CoverageReport(
        source=source,
        start_utc=win.start_utc,
        effective_end=end,
        records_in_window=len(in_window),
        variables=variables,
        state=state_of(len(in_window), variables),
        missing=missing_steps(expected, in_window),
    )
