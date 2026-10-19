"""Modelos de calendario: valor típico de una variable según la hora del día y la estación.

Cada modelo es una regresión lineal cuya única entrada es la fecha y hora local (D-024).
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

from clima_medellin.config import LOCAL_TZ
from clima_medellin.coverage import Window
from clima_medellin.split import Split

TARGETS = ["temperature_2m_c", "relative_humidity_2m_pct", "pm25_ug_m3"]
HOUR_COLUMNS = [f"h{h:02d}" for h in range(1, 24)]  # 00:00 es la referencia
FEATURES = HOUR_COLUMNS + ["season_sin", "season_cos"]
DAYS_PER_YEAR = 365.25
MAX_DAYS = 31
MAX_DAYS_AHEAD = 365


def calendar_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Rasgos de calendario en hora de Medellín: un indicador por hora y la onda estacional."""
    local = index.tz_convert(LOCAL_TZ)
    hours = local.hour.to_numpy()
    # Una columna 0/1 por hora (codificación one-hot); las 00:00 quedan con todo a 0.
    features = {name: (hours == h).astype(float) for h, name in enumerate(HOUR_COLUMNS, start=1)}
    # El año es un círculo: seno y coseno sitúan cada día sobre él, así el 31 de
    # diciembre queda junto al 1 de enero.
    angle = 2 * np.pi * local.dayofyear.to_numpy() / DAYS_PER_YEAR
    features["season_sin"] = np.sin(angle)
    features["season_cos"] = np.cos(angle)
    return pd.DataFrame(features, index=index)[FEATURES]


@dataclass
class CalendarModel:
    variable: str
    final: LinearRegression
    metrics: pd.DataFrame
    typical_error: float
    intercept: float
    hour_effects: pd.Series
    season_sin: float
    season_cos: float
    n_train: int
    n_test: int
    n_all: int

    def predict(self, index: pd.DatetimeIndex) -> np.ndarray:
        return self.final.predict(calendar_features(index))


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": root_mean_squared_error(y_true, y_pred),
        "R2": r2_score(y_true, y_pred),
    }


def fit_calendar_model(frame: pd.DataFrame, variable: str, split: Split) -> CalendarModel:
    """Evalúa con la separación temporal y reajusta con toda la ventana para predecir."""
    series = frame[variable].dropna()
    train, test = split.train(series.to_frame())[variable], split.test(series.to_frame())[variable]
    if train.empty or test.empty:
        raise ValueError(
            f"No hay datos suficientes de {variable} para el modelo de calendario "
            f"({len(train)} horas de entrenamiento y {len(test)} de prueba)."
        )
    # 1. Evaluación: se ajusta solo con el entrenamiento y se mide en la prueba.
    evaluation = LinearRegression().fit(calendar_features(train.index), train)
    predicted = evaluation.predict(calendar_features(test.index))
    baseline = np.full(len(test), train.mean())
    metrics = pd.DataFrame(
        {"modelo": _metrics(test, predicted), "linea_base": _metrics(test, baseline)}
    ).T

    # 2. Reajuste con todas las horas de la ventana: es el modelo que predice.
    final = LinearRegression().fit(calendar_features(series.index), series)
    coefficients = pd.Series(final.coef_, index=FEATURES)
    hour_effects = pd.Series([0.0] + [coefficients[c] for c in HOUR_COLUMNS], index=range(24))
    return CalendarModel(
        variable=variable,
        final=final,
        metrics=metrics,
        typical_error=float(metrics.loc["modelo", "MAE"]),
        intercept=float(final.intercept_),
        hour_effects=hour_effects,
        season_sin=float(coefficients["season_sin"]),
        season_cos=float(coefficients["season_cos"]),
        n_train=len(train),
        n_test=len(test),
        n_all=len(series),
    )


def fit_calendar_models(frame: pd.DataFrame, split: Split) -> dict[str, CalendarModel]:
    return {variable: fit_calendar_model(frame, variable, split) for variable in TARGETS}


# --- Peticiones de predicción ------------------------------------------------------------


class PredictionRequestError(ValueError):
    """La petición de predicción no tiene un formato válido o se sale de los límites."""


FORMAT_HELP = "usa AAAA-MM-DD, AAAA-MM-DD HH o AAAA-MM-DD HH:MM (ej. 2026-11-03 15:00)"
_MOMENT = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2})(?::(\d{2}))?)?$")


def parse_moment(text: str) -> tuple[datetime, bool]:
    """Interpreta una fecha u hora local; devuelve el instante y si se indicó la hora."""
    match = _MOMENT.match(text.strip())
    if not match:
        raise PredictionRequestError(f"«{text.strip()}» no es una fecha válida: {FORMAT_HELP}.")
    day_text, hour_text, minute_text = match.groups()
    try:
        day = date.fromisoformat(day_text)
    except ValueError as exc:
        raise PredictionRequestError(f"«{day_text}» no es un día que exista.") from exc
    if hour_text is None:
        return datetime.combine(day, time.min, tzinfo=LOCAL_TZ), False
    hour = int(hour_text)
    if hour > 23 or (minute_text is not None and minute_text != "00"):
        raise PredictionRequestError(
            f"«{text.strip()}»: la hora debe ser exacta, de 00:00 a 23:00 (los datos son horarios)."
        )
    return datetime.combine(day, time(hour), tzinfo=LOCAL_TZ), True


def request_hours(start_text: str, end_text: str, win: Window, today: date) -> pd.DatetimeIndex:
    """Horas (UTC) de una petición: una hora, un día completo o un rango con ambos extremos."""
    start, start_has_hour = parse_moment(start_text)
    if end_text.strip():
        end, end_has_hour = parse_moment(end_text)
        if not end_has_hour:
            end = end.replace(hour=23)  # una fecha como «hasta» incluye todo ese día
    else:
        end = start if start_has_hour else start.replace(hour=23)
    if end < start:
        raise PredictionRequestError("«Hasta» es anterior a «Desde».")
    first_allowed = pd.Timestamp(win.start_utc).tz_convert(LOCAL_TZ)
    if pd.Timestamp(start) < first_allowed:
        raise PredictionRequestError(
            f"Solo se puede predecir desde el inicio de los datos guardados ({win.start_local}): "
            "el modelo no ha visto fechas anteriores."
        )
    limit = datetime.combine(today + timedelta(days=MAX_DAYS_AHEAD + 1), time.min, tzinfo=LOCAL_TZ)
    if end >= limit:
        raise PredictionRequestError(
            f"Solo se puede predecir hasta un año después de hoy "
            f"({today + timedelta(days=MAX_DAYS_AHEAD)}): el modelo solo conoce un ciclo "
            "de estaciones."
        )
    hours = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="h")
    if len(hours) > MAX_DAYS * 24:
        raise PredictionRequestError(
            f"El rango abarca {len(hours)} horas; el máximo es {MAX_DAYS} días "
            f"({MAX_DAYS * 24} horas)."
        )
    return hours.tz_convert("UTC")


def predict(
    models: dict[str, CalendarModel],
    hours: pd.DatetimeIndex,
    actual: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Predicción por hora local; con datos guardados añade el valor real y la diferencia."""
    pieces = {}
    for variable, model in models.items():
        predicted = pd.Series(model.predict(hours), index=hours)
        real = (
            actual[variable].reindex(hours)
            if actual is not None and variable in actual
            else pd.Series(np.nan, index=hours)
        )
        pieces[variable] = pd.DataFrame(
            {"prediccion": predicted, "real": real, "diferencia": real - predicted}
        )
    table = pd.concat(pieces, axis=1)
    table.index = hours.tz_convert(LOCAL_TZ)
    table.index.name = "hora_local"
    return table
