"""Pruebas del cliente HTTP sin red: una sesión falsa devuelve respuestas programadas."""

from datetime import date

import pytest
import requests

from clima_medellin.openmeteo import OpenMeteoError, build_request, fetch

START, END = date(2026, 3, 1), date(2026, 3, 31)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


class FakeSession:
    """Devuelve (o lanza) los resultados programados, uno por llamada."""

    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_era5_request_uses_locked_params():
    url, params = build_request("ERA5", START, END)
    assert url == "https://archive-api.open-meteo.com/v1/archive"
    assert params["models"] == "era5"
    assert params["elevation"] == 1495
    assert params["wind_speed_unit"] == "ms"
    assert params["hourly"] == "temperature_2m,relative_humidity_2m,wind_speed_10m"
    assert (params["latitude"], params["longitude"]) == (6.2447, -75.5748)
    assert params["timezone"] == "GMT"
    assert (params["start_date"], params["end_date"]) == ("2026-03-01", "2026-03-31")


def test_pm25_request_has_no_elevation():
    url, params = build_request("CAMS_GLOBAL", START, END)
    assert url == "https://air-quality-api.open-meteo.com/v1/air-quality"
    assert params["hourly"] == "pm2_5"
    assert params["domains"] == "cams_global"
    assert "elevation" not in params


def test_transient_errors_are_retried_with_growing_waits():
    waits = []
    session = FakeSession(FakeResponse(503), FakeResponse(503), FakeResponse(200, {"ok": 1}))
    assert fetch("ERA5", START, END, session=session, sleep=waits.append) == {"ok": 1}
    assert len(session.calls) == 3
    assert waits == [1, 2]


def test_gives_up_after_three_retries_naming_source_and_range():
    waits = []
    session = FakeSession(*[requests.Timeout() for _ in range(4)])
    with pytest.raises(OpenMeteoError) as exc:
        fetch("CAMS_GLOBAL", START, END, session=session, sleep=waits.append)
    assert len(session.calls) == 4
    assert waits == [1, 2, 4]
    assert "CAMS_GLOBAL" in str(exc.value) and "2026-03-01" in str(exc.value)


def test_connection_error_is_retried():
    session = FakeSession(requests.ConnectionError(), FakeResponse(200, {"ok": 1}))
    assert fetch("ERA5", START, END, session=session, sleep=lambda s: None) == {"ok": 1}


def test_client_error_is_not_retried():
    session = FakeSession(FakeResponse(400), FakeResponse(200))
    with pytest.raises(OpenMeteoError, match="HTTP 400"):
        fetch("ERA5", START, END, session=session, sleep=lambda s: None)
    assert len(session.calls) == 1
