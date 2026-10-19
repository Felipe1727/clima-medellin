"""Cliente HTTP de las APIs de Open-Meteo (Historical Weather y Air Quality)."""

import time
from collections.abc import Callable
from datetime import date

import requests

from clima_medellin.config import SOURCES

TIMEOUT_S = 60
# Esperas antes de cada reintento: 3 reintentos tras el primer intento.
RETRY_DELAYS_S = (1, 2, 4)


class OpenMeteoError(Exception):
    """La petición a Open-Meteo no se pudo completar."""


def build_request(source: str, start: date, end: date) -> tuple[str, dict]:
    """Devuelve la URL y los parámetros para pedir una fuente entre dos fechas (inclusive)."""
    config = SOURCES[source]
    params = {
        **config.fixed_params,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    return config.url, params


def fetch(
    source: str,
    start: date,
    end: date,
    *,
    session: requests.Session | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Descarga una fuente y devuelve el JSON decodificado.

    Reintenta ante tiempos de espera agotados, errores de conexión y respuestas 5xx;
    una respuesta 4xx es un error de la petición y no se reintenta.
    """
    url, params = build_request(source, start, end)
    http = session or requests.Session()
    label = f"{source} {start.isoformat()} → {end.isoformat()}"
    last_problem = ""
    for attempt in range(len(RETRY_DELAYS_S) + 1):
        if attempt > 0:
            sleep(RETRY_DELAYS_S[attempt - 1])
        try:
            response = http.get(url, params=params, timeout=TIMEOUT_S)
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_problem = type(exc).__name__
            continue
        if response.status_code >= 500:
            last_problem = f"HTTP {response.status_code}"
            continue
        if response.status_code != 200:
            raise OpenMeteoError(f"{label}: la API respondió HTTP {response.status_code}")
        return response.json()
    raise OpenMeteoError(
        f"{label}: sin respuesta válida tras {len(RETRY_DELAYS_S)} reintentos ({last_problem})"
    )
