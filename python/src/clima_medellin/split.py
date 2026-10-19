"""Separación temporal de la ventana: entrenamiento, hueco de 24 h y prueba (D-018)."""

import calendar
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

import pandas as pd

from clima_medellin.config import LOCAL_TZ
from clima_medellin.coverage import Window

TRAIN_MONTHS = 9
GAP = timedelta(hours=24)


def add_months(day: date, months: int) -> date:
    """Suma meses naturales; si el día no existe en el mes final, usa el último día."""
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


@dataclass(frozen=True)
class Split:
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime

    def train(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Filas de [train_start, train_end)."""
        return _between(frame, self.train_start, self.train_end)

    def test(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Filas de [test_start, test_end)."""
        return _between(frame, self.test_start, self.test_end)


def _between(frame: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    mask = (frame.index >= pd.Timestamp(start)) & (frame.index < pd.Timestamp(end))
    return frame[mask]


def temporal_split(win: Window) -> Split:
    """Entrenamiento de 9 meses naturales, 24 h descartadas y prueba hasta el fin."""
    train_end_local = add_months(win.start_local, TRAIN_MONTHS)
    train_end = datetime.combine(train_end_local, time.min, tzinfo=LOCAL_TZ).astimezone(UTC)
    return Split(win.start_utc, train_end, train_end + GAP, win.end_utc)
