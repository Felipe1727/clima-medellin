"""Menú de terminal de 7 opciones: una capa fina sobre las funciones del proyecto."""

import math
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

from clima_medellin import coverage as cov
from clima_medellin import openmeteo, paths, plots
from clima_medellin.bands import daily_bands
from clima_medellin.bridge import BridgeError, JavaBridge
from clima_medellin.config import LOCAL_TZ, LOCATION, SOURCES
from clima_medellin.dataset import load_window
from clima_medellin.descriptive import describe_bands, describe_variables
from clima_medellin.normalize import NormalizationError
from clima_medellin.openmeteo import OpenMeteoError
from clima_medellin.regression import fit_and_evaluate, regression_dataset
from clima_medellin.split import temporal_split
from clima_medellin.update import UpdatePlan, current_coverage, execute_plan, plan_update

OPTIONS = {
    "1": "Verificar cobertura",
    "2": "Actualizar datos",
    "3": "Consultar registros",
    "4": "Estadísticas descriptivas",
    "5": "Entrenar y evaluar la regresión",
    "6": "Generar visualizaciones",
    "7": "Salir",
}
SOURCE_NAMES = {"ERA5": "ERA5 (meteorología)", "CAMS_GLOBAL": "CAMS global (PM2.5)"}
PAGE_SIZE = 20
# Open-Meteo cuenta como varias llamadas las peticiones de más de 2 semanas.
DAYS_PER_CALL = 14
DAILY_LIMIT = 10_000
ERRORS = (BridgeError, OpenMeteoError, NormalizationError, ValueError)


class Menu:
    def __init__(
        self,
        bridge: JavaBridge,
        *,
        fetch: Callable = openmeteo.fetch,
        today: date | None = None,
        outputs_dir: Path = paths.OUTPUTS_DIR,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
    ):
        self.bridge = bridge
        self.fetch = fetch
        self.fixed_today = today
        self.outputs_dir = outputs_dir
        self.input = input_fn
        self.print = print_fn
        self.actions = {
            "1": self.show_coverage,
            "2": self.update_data,
            "3": self.query_records,
            "4": self.show_statistics,
            "5": self.run_regression,
            "6": self.make_charts,
        }

    # --- utilidades --------------------------------------------------------------------

    def today(self) -> date:
        return self.fixed_today or cov.today_local()

    def ok(self, text: str) -> None:
        self.print(f"[OK] {text}")

    def progress(self, text: str) -> None:
        self.print(f"[…] {text}")

    def warn(self, text: str) -> None:
        self.print(f"[AVISO] {text}")

    def error(self, text: str) -> None:
        self.print(f"[ERROR] {text}")

    def confirm(self, question: str) -> bool:
        return self.input(f"{question} [s/N] ").strip().lower() in {"s", "si", "sí"}

    def header(self) -> None:
        win = cov.window(self.today())
        self.print("")
        self.print("  CLIMA MEDELLÍN · Bases de Datos")
        self.print(
            f"  Ubicación: {LOCATION.code} · Ventana: {win.start_local} → {win.end_local} "
            f"({LOCATION.timezone})"
        )
        self.print("")
        for key, text in OPTIONS.items():
            self.print(f"  {key}) {text}")
        self.print("")

    # --- bucle principal ---------------------------------------------------------------

    def run(self) -> None:
        while True:
            self.header()
            try:
                choice = self.input("  Opción: ").strip()
            except EOFError, KeyboardInterrupt:
                choice = "7"
            if choice == "7":
                self.print("Hasta pronto.")
                return
            action = self.actions.get(choice)
            if action is None:
                self.error(f"Opción no válida: {choice!r}. Elige un número del 1 al 7.")
                continue
            try:
                action()
            except ERRORS as exc:
                # Ningún error cierra la aplicación: se informa y se vuelve al menú.
                self.error(str(exc))

    # --- opción 1 ----------------------------------------------------------------------

    def show_coverage(self) -> dict[str, cov.CoverageReport]:
        reports = current_coverage(self.bridge, self.today())
        for source, report in reports.items():
            self.print("")
            self.print(
                f"{SOURCE_NAMES[source]} · fin efectivo "
                f"{report.effective_end:%Y-%m-%d %H:%M} UTC · estado {report.state}"
            )
            table = pd.DataFrame(
                [
                    {
                        "variable": plots.NAMES[v.column],
                        "esperados": v.expected,
                        "válidos": v.valid,
                        "cobertura %": round(v.percent, 2),
                        "hueco máx. (h)": v.max_gap_hours,
                        "huecos": v.gaps,
                    }
                    for v in report.variables
                ]
            )
            self.print(table.to_string(index=False))
            intervals = sorted(
                cov.group_intervals(report.missing), key=lambda i: i[1] - i[0], reverse=True
            )[:3]
            for first, last in intervals:
                hours = int((last - first) / cov.STEP) + 1
                self.print(
                    f"  Faltan {hours} h: {first.tz_convert(LOCAL_TZ):%Y-%m-%d %H:%M} → "
                    f"{last.tz_convert(LOCAL_TZ):%Y-%m-%d %H:%M} (hora local)"
                )
        return reports

    # --- opción 2 ----------------------------------------------------------------------

    def update_data(self) -> None:
        plan = plan_update(self.bridge, self.today())
        if not plan.requests:
            self.ok("No hay nada que descargar: la base está al día.")
            return
        calls = sum(math.ceil(r.days / DAYS_PER_CALL) for r in plan.requests)
        self.print("Plan de descarga:")
        for request in plan.requests:
            self.print(
                f"  {request.source}: {request.start_date} → {request.end_date} "
                f"({request.days} días)"
            )
        limit = f"{DAILY_LIMIT:_}".replace("_", ".")
        question = (
            f"Se pedirán {len(plan.requests)} intervalos (≈ {calls} llamadas equivalentes "
            f"de un máximo de {limit} diarias). ¿Continuar?"
        )
        if not self.confirm(question):
            self.print("Actualización cancelada.")
            return
        for i, request in enumerate(plan.requests, start=1):
            self.progress(
                f"Descargando {request.source} {request.start_date} → {request.end_date} "
                f"({i}/{len(plan.requests)})"
            )
            single = UpdatePlan(today=plan.today, window=plan.window, requests=[request])
            try:
                (result,) = execute_plan(self.bridge, single, fetch=self.fetch)
            except ERRORS as exc:
                # Los intervalos ya importados se conservan; este se reintentará la próxima vez.
                self.error(
                    f"Falló {request.source} {request.start_date} → {request.end_date}: {exc}"
                )
                continue
            imported = result.imported
            self.ok(
                f"Lote importado: {imported['received']} recibidos, {imported['inserted']} "
                f"insertados, {imported['duplicates']} duplicados omitidos, "
                f"{imported['rejected']} rechazados."
            )
        self.print("Cobertura resultante:")
        self.show_coverage()

    # --- reglas comunes de las opciones 3 a 6 --------------------------------------------

    def guard(self) -> bool:
        """Avisa si la cobertura no es COMPLETA; con la base vacía sugiere la opción 2."""
        reports = current_coverage(self.bridge, self.today())
        states = {source: report.state for source, report in reports.items()}
        if all(state == "SIN_DATOS" for state in states.values()):
            self.warn("La base está vacía. Ejecuta primero la opción 2 (Actualizar datos).")
            return False
        partial = [f"{s} {state}" for s, state in states.items() if state != "COMPLETA"]
        if partial:
            self.warn(
                f"Cobertura no COMPLETA ({', '.join(partial)}). Los resultados pueden estar "
                "sesgados."
            )
            return self.confirm("¿Continuar de todos modos?")
        return True

    def window_frame(self) -> tuple[cov.Window, pd.DataFrame]:
        win = cov.window(self.today())
        return win, load_window(self.bridge, win)

    # --- opción 3 ----------------------------------------------------------------------

    def query_records(self) -> None:
        if not self.guard():
            return
        answer = self.input("Fuente (1 = ERA5, 2 = CAMS global): ").strip()
        source = {"1": "ERA5", "2": "CAMS_GLOBAL"}.get(answer)
        if source is None:
            self.error("Fuente no válida.")
            return
        try:
            first = date.fromisoformat(self.input("Desde (AAAA-MM-DD, hora local): ").strip())
            last = date.fromisoformat(self.input("Hasta (AAAA-MM-DD, inclusive): ").strip())
        except ValueError:
            self.error("Fecha no válida; usa el formato AAAA-MM-DD.")
            return
        start = datetime.combine(first, time.min, tzinfo=LOCAL_TZ)
        end = datetime.combine(last + timedelta(days=1), time.min, tzinfo=LOCAL_TZ)
        frame = self.bridge.export(source, start, end)
        columns = SOURCES[source].columns
        if frame.empty:
            self.ok("0 registros en ese rango.")
            return
        table = pd.DataFrame(
            {
                "hora local": frame.index.tz_convert(LOCAL_TZ).strftime("%Y-%m-%d %H:%M"),
                "UTC": frame.index.strftime("%Y-%m-%d %H:%M"),
                **{
                    plots.label(c): frame[c].map(lambda v: "—" if pd.isna(v) else f"{v:g}")
                    for c in columns
                },
                "lote": frame["batch_id"].str[:8],
            }
        )
        for page_start in range(0, len(table), PAGE_SIZE):
            page = table.iloc[page_start : page_start + PAGE_SIZE]
            self.print(page.to_string(index=False))
            if page_start + PAGE_SIZE < len(table):
                more = self.input("Enter = siguiente página, q = terminar: ").strip().lower()
                if more == "q":
                    break
        nulls = int(frame[columns].isna().sum().sum())
        self.ok(f"{len(frame)} registros, {nulls} valores nulos.")

    # --- opción 4 ----------------------------------------------------------------------

    def show_statistics(self) -> None:
        if not self.guard():
            return
        win, frame = self.window_frame()
        stats = describe_variables(frame).round(2)
        stats.index = [plots.label(c) for c in stats.index]
        self.print(f"Estadísticas por variable ({win.start_local} → {win.end_local}):")
        self.print(stats.to_string())
        bands = describe_bands(daily_bands(frame)).round(2)
        bands.index = bands.index.set_levels(
            [plots.label(c) for c in bands.index.levels[0]], level=0
        )
        self.print("Medias por franja (07–09, 13–15 y 19–21 h locales; días válidos):")
        self.print(bands.to_string())

    # --- opción 5 ----------------------------------------------------------------------

    def run_regression(self) -> None:
        if not self.guard():
            return
        win, frame = self.window_frame()
        data, excluded = regression_dataset(frame)
        split = temporal_split(win)
        result = fit_and_evaluate(data, split)
        local = {k: pd.Timestamp(v).tz_convert(LOCAL_TZ) for k, v in vars(split).items()}
        self.print(
            f"Entrenamiento: {local['train_start']:%Y-%m-%d %H:%M} → "
            f"{local['train_end']:%Y-%m-%d %H:%M} ({result.n_train} horas) · hueco de 24 h · "
            f"prueba: {local['test_start']:%Y-%m-%d %H:%M} → {local['test_end']:%Y-%m-%d %H:%M} "
            f"({result.n_test} horas), hora local. Filas excluidas por nulos: {excluded}."
        )
        self.print("Métricas en la prueba (µg/m³ salvo R²):")
        self.print(result.metrics.round(3).to_string())
        self.print(
            f"Coeficientes (intercepto {result.intercept_std:.3f} µg/m³ estandarizado, "
            f"{result.intercept_original:.3f} en unidades originales):"
        )
        coefficients = result.coefficients.assign(VIF=result.vif).round(3)
        coefficients.index = [plots.label(c) for c in coefficients.index]
        self.print(coefficients.to_string())
        self.print(f"Durbin-Watson de los residuos de prueba: {result.durbin_watson:.3f}")
        self.print(
            "Lectura prudente: describe una asociación en los modelos ERA5 y CAMS, no un "
            "efecto causal ni una validación con mediciones (ver docs/regresion.md)."
        )

    # --- opción 6 ----------------------------------------------------------------------

    def make_charts(self) -> None:
        if not self.guard():
            return
        answer = self.input("Salida (1 = ventana, 2 = PNG): ").strip()
        mode = {"1": "ventana", "2": "png"}.get(answer)
        if mode is None:
            self.error("Opción de salida no válida.")
            return
        win, frame = self.window_frame()
        split = temporal_split(win)
        data, _ = regression_dataset(frame)
        result = fit_and_evaluate(data, split)
        start, end = win.start_utc, win.end_utc
        figures = {
            f"serie_{c}": lambda c=c: plots.time_series(frame, c, start, end) for c in frame.columns
        }
        figures |= {
            "perfil_diurno": lambda: plots.diurnal_profile(frame, split),
            "franjas": lambda: plots.band_boxplots(daily_bands(frame), start, end),
            "dispersion": lambda: plots.scatter_predictors(data, split),
            "correlacion": lambda: plots.correlation_matrix(data, split),
            "empalmes": lambda: plots.seam_diagnostic(frame["pm25_ug_m3"], start, end),
            "real_predicho": lambda: plots.actual_vs_predicted(result),
            "residuos": lambda: plots.residuals(result),
        }
        for source in SOURCES:
            existing = self.bridge.coverage(source).existing
            figures[f"cobertura_{source}"] = lambda e=existing, s=source: plots.coverage_map(
                e, s, start, end
            )
        for name, build in figures.items():
            output = plots.save_or_show(build(), name, mode, self.outputs_dir)
            if output.notice:
                self.warn(output.notice)
            elif output.path:
                self.ok(f"Gráfica guardada: {output.path}")
        self.ok(f"{len(figures)} gráficas generadas.")
