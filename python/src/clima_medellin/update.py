"""Actualización incremental: descargar solo lo que falta (D-015)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pandas as pd

from clima_medellin import coverage as cov
from clima_medellin import openmeteo
from clima_medellin.bridge import JavaBridge
from clima_medellin.config import SOURCES
from clima_medellin.normalize import NormalizationReport, normalize

Fetch = Callable[[str, date, date], dict]


@dataclass(frozen=True)
class PlannedRequest:
    source: str
    start_date: date
    end_date: date

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days + 1


@dataclass(frozen=True)
class UpdatePlan:
    today: date
    window: cov.Window
    requests: list[PlannedRequest]


@dataclass(frozen=True)
class RequestResult:
    request: PlannedRequest
    normalization: NormalizationReport
    outside_window: int
    imported: dict


@dataclass(frozen=True)
class UpdateOutcome:
    plan: UpdatePlan
    results: list[RequestResult]
    coverage: dict[str, cov.CoverageReport]


def current_coverage(bridge: JavaBridge, today: date) -> dict[str, cov.CoverageReport]:
    """Cobertura de cada fuente a partir de lo guardado en la base."""
    win = cov.window(today)
    return {
        source: cov.coverage_report(source, bridge.coverage(source).existing, win, today)
        for source in SOURCES
    }


def plan_update(bridge: JavaBridge, today: date) -> UpdatePlan:
    """Peticiones por rango de fechas que cubren los pasos esperados sin registro."""
    win = cov.window(today)
    requests = []
    for source, report in current_coverage(bridge, today).items():
        for start, end in cov.to_request_dates(cov.group_intervals(report.missing)):
            requests.append(PlannedRequest(source, start, end))
    return UpdatePlan(today=today, window=win, requests=requests)


def execute_plan(
    bridge: JavaBridge, plan: UpdatePlan, *, fetch: Fetch = openmeteo.fetch
) -> list[RequestResult]:
    """Descarga, normaliza, recorta a la ventana e importa cada petición del plan."""
    results = []
    for request in plan.requests:
        end = cov.effective_end(request.source, plan.window, plan.today)
        payload = fetch(request.source, request.start_date, request.end_date)
        normalized = normalize(request.source, payload, end)
        # La petición pide días UTC completos: el primero empieza antes de la ventana.
        before = normalized.frame.index < pd.Timestamp(plan.window.start_utc)
        frame = normalized.frame[~before]
        url, params = openmeteo.build_request(request.source, request.start_date, request.end_date)
        requested_start = datetime.combine(request.start_date, time.min, tzinfo=end.tzinfo)
        # Se importa aunque la tabla esté vacía: el lote con 0 insertados deja constancia.
        imported = bridge.import_frame(
            request.source,
            frame,
            requested_start=requested_start,
            requested_end=min(requested_start + timedelta(days=request.days), end),
            endpoint=url,
            params=params,
        )
        results.append(RequestResult(request, normalized.report, int(before.sum()), imported))
    return results


def update(bridge: JavaBridge, today: date, *, fetch: Fetch = openmeteo.fetch) -> UpdateOutcome:
    """Cobertura → plan → descarga → normalización → importación → nueva cobertura."""
    plan = plan_update(bridge, today)
    results = execute_plan(bridge, plan, fetch=fetch)
    return UpdateOutcome(plan, results, current_coverage(bridge, today))
