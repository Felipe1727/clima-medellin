"""Menú de terminal: una capa fina sobre las funciones del proyecto, presentada con rich."""

import math
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from clima_medellin import coverage as cov
from clima_medellin import openmeteo, paths, plots, ui
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

# Menú agrupado por lo que el usuario quiere hacer (D-025); el término técnico va entre paréntesis.
GROUPS = {
    "DATOS": {
        "1": "Ver qué datos hay guardados (cobertura)",
        "2": "Descargar los datos que faltan (actualizar)",
        "3": "Consultar registros por fecha",
    },
    "ANÁLISIS": {
        "4": "Resumen estadístico (medias, rangos, franjas)",
        "5": "Evaluar los modelos (qué tan bien predicen)",
    },
    "PREDICCIONES": {
        "6": "Predecir temperatura, humedad o PM2.5 para una fecha u hora",
        "7": "Generar gráficas",
    },
}
SOURCE_NAMES = {"ERA5": "ERA5 (meteorología)", "CAMS_GLOBAL": "CAMS global (PM2.5)"}
PAGE_SIZE = 20
# Open-Meteo cuenta como varias llamadas las peticiones de más de 2 semanas.
DAYS_PER_CALL = 14
DAILY_LIMIT = 10_000
ERRORS = (BridgeError, OpenMeteoError, NormalizationError, ValueError)
DB_STATES = {
    "al día": ("green", "las dos fuentes están completas"),
    "incompleta": ("yellow", "faltan datos: usa la opción 2 para descargarlos"),
    "vacía": ("red", "no hay datos: empieza por la opción 2"),
    "desconocido": ("yellow", "no se pudo consultar la base"),
}


class Menu:
    def __init__(
        self,
        bridge: JavaBridge,
        *,
        console: Console | None = None,
        fetch: Callable = openmeteo.fetch,
        today: date | None = None,
        outputs_dir: Path = paths.OUTPUTS_DIR,
        input_fn: Callable[[str], str] | None = None,
    ):
        self.bridge = bridge
        self.console = console or ui.make_console()
        self.fetch = fetch
        self.fixed_today = today
        self.outputs_dir = outputs_dir
        self.input = input_fn or self.console.input
        self._db_state: str | None = None
        self.actions = {
            "1": self.show_coverage,
            "2": self.update_data,
            "3": self.query_records,
            "4": self.show_statistics,
            "5": self.run_regression,
            "6": self.predict_soon,
            "7": self.make_charts,
        }

    # --- utilidades --------------------------------------------------------------------

    def today(self) -> date:
        return self.fixed_today or cov.today_local()

    def print(self, *objects) -> None:
        self.console.print(*objects)

    def confirm(self, question: str) -> bool:
        return self.input(f"{question} [s/N] ").strip().lower() in {"s", "si", "sí"}

    def progress(self) -> Progress:
        """Barra de progreso; desactivada si la salida no es una terminal (pruebas, archivos)."""
        return Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=self.console,
            transient=True,
            disable=not self.console.is_terminal,
        )

    def db_state(self) -> str:
        """Estado de la base para la cabecera; se calcula una vez y se renueva tras descargar."""
        if self._db_state is None:
            try:
                states = {r.state for r in current_coverage(self.bridge, self.today()).values()}
            except ERRORS:
                return "desconocido"
            if states == {"COMPLETA"}:
                self._db_state = "al día"
            elif states == {"SIN_DATOS"}:
                self._db_state = "vacía"
            else:
                self._db_state = "incompleta"
        return self._db_state

    def header(self) -> None:
        win = cov.window(self.today())
        state = self.db_state()
        style, hint = DB_STATES[state]
        lines = Text.assemble(
            ("CLIMA MEDELLÍN · Bases de Datos\n", "bold"),
            f"Ubicación: {LOCATION.name} ({LOCATION.code})\n",
            f"Datos del último año: {win.start_local} → {win.end_local} (hora de Medellín)\n",
            "Base de datos: ",
            (state, f"bold {style}"),
            f" · {hint}",
        )
        self.print(Panel(lines, border_style="cyan", expand=False))
        for group, options in GROUPS.items():
            self.print(Text(f" {group}", style="bold cyan"))
            for key, text in options.items():
                self.print(f"   {key}  {text}")
        self.print("\n   0  Salir\n")

    # --- bucle principal ---------------------------------------------------------------

    def run(self) -> None:
        while True:
            self.header()
            try:
                choice = self.input("Elige una opción (0-7): ").strip()
            except EOFError, KeyboardInterrupt:
                choice = "0"
            if choice == "0":
                self.print("Hasta pronto.")
                return
            action = self.actions.get(choice)
            if action is None:
                self.print(ui.error(f"Opción no válida: {choice!r}. Escribe un número del 0 al 7."))
                continue
            try:
                action()
            except ERRORS as exc:
                # Ningún error cierra la aplicación: se informa y se vuelve al menú.
                self.print(ui.error(str(exc)))

    # --- opción 1 ----------------------------------------------------------------------

    def show_coverage(self, *, explain: bool = True) -> dict[str, cov.CoverageReport]:
        reports = current_coverage(self.bridge, self.today())
        for source, report in reports.items():
            frame = pd.DataFrame(
                [
                    {
                        "variable": plots.NAMES[v.column],
                        "horas esperadas": v.expected,
                        "horas con dato": v.valid,
                        "cobertura (%)": round(v.percent, 2),
                        "hueco más largo (h)": v.max_gap_hours,
                        "huecos": v.gaps,
                    }
                    for v in report.variables
                ]
            ).set_index("variable")
            title = Text.assemble(
                (SOURCE_NAMES[source], "bold"),
                f" · datos hasta {report.effective_end.astimezone(LOCAL_TZ):%Y-%m-%d %H:%M} · ",
                ui.state_text(report.state),
            )
            self.print(ui.df_table(frame, index_name="variable"))
            self.print(title)
            intervals = sorted(
                cov.group_intervals(report.missing), key=lambda i: i[1] - i[0], reverse=True
            )[:3]
            for first, last in intervals:
                hours = int((last - first) / cov.STEP) + 1
                self.print(
                    f"  Faltan {hours} h: {first.tz_convert(LOCAL_TZ):%Y-%m-%d %H:%M} → "
                    f"{last.tz_convert(LOCAL_TZ):%Y-%m-%d %H:%M} (hora local)"
                )
        if explain:
            self.print(
                ui.meaning(
                    "La cobertura es el porcentaje de horas del último año que tienen dato. "
                    "COMPLETA significa al menos un 98 % y ningún hueco de más de 6 horas "
                    "seguidas; con menos, los resultados pueden estar sesgados. La meteorología "
                    "(ERA5) se publica con 5 días de retraso, por eso termina antes que el PM2.5."
                )
            )
        return reports

    # --- opción 2 ----------------------------------------------------------------------

    def update_data(self) -> None:
        plan = plan_update(self.bridge, self.today())
        if not plan.requests:
            self.print(ui.ok("No hay nada que descargar: la base está al día."))
            return
        calls = sum(math.ceil(r.days / DAYS_PER_CALL) for r in plan.requests)
        table = Table(title="Plan de descarga", title_justify="left", header_style="bold cyan")
        for column in ("fuente", "desde", "hasta", "días"):
            table.add_column(column)
        for request in plan.requests:
            table.add_row(
                SOURCE_NAMES[request.source],
                str(request.start_date),
                str(request.end_date),
                str(request.days),
            )
        self.print(table)
        limit = f"{DAILY_LIMIT:_}".replace("_", ".")
        question = (
            f"Se pedirán {len(plan.requests)} intervalos (≈ {calls} llamadas equivalentes "
            f"de un máximo de {limit} diarias). ¿Continuar?"
        )
        if not self.confirm(question):
            self.print("Actualización cancelada.")
            return
        inserted = 0
        with self.progress() as bar:
            task = bar.add_task("Descargando", total=len(plan.requests))
            for i, request in enumerate(plan.requests, start=1):
                self.print(
                    ui.progress_line(
                        f"Descargando {request.source} {request.start_date} → "
                        f"{request.end_date} ({i}/{len(plan.requests)})"
                    )
                )
                single = UpdatePlan(today=plan.today, window=plan.window, requests=[request])
                try:
                    (result,) = execute_plan(self.bridge, single, fetch=self.fetch)
                except ERRORS as exc:
                    # Los intervalos ya importados se conservan; este se reintentará después.
                    self.print(
                        ui.error(
                            f"Falló {request.source} {request.start_date} → "
                            f"{request.end_date}: {exc}"
                        )
                    )
                    continue
                finally:
                    bar.advance(task)
                imported = result.imported
                inserted += imported["inserted"]
                self.print(
                    ui.ok(
                        f"Lote importado: {imported['received']} recibidos, "
                        f"{imported['inserted']} insertados, {imported['duplicates']} duplicados "
                        f"omitidos, {imported['rejected']} rechazados."
                    )
                )
        self._db_state = None
        self.print(Text("Cobertura resultante:", style="bold"))
        self.show_coverage(explain=False)
        self.print(
            ui.meaning(
                f"Se guardaron {inserted} horas nuevas. Solo se descarga lo que falta: si vuelves "
                "a elegir esta opción, no se repetirá nada de lo ya guardado. «Duplicados "
                "omitidos» son horas que ya estaban en la base y no se tocaron."
            )
        )

    # --- reglas comunes de las opciones 3 a 7 --------------------------------------------

    def guard(self) -> bool:
        """Avisa si la cobertura no es COMPLETA; con la base vacía sugiere la opción 2."""
        reports = current_coverage(self.bridge, self.today())
        states = {source: report.state for source, report in reports.items()}
        if all(state == "SIN_DATOS" for state in states.values()):
            self.print(ui.warn("La base está vacía. Ejecuta primero la opción 2 (Descargar)."))
            return False
        partial = [f"{s} {state}" for s, state in states.items() if state != "COMPLETA"]
        if partial:
            self.print(
                ui.warn(
                    f"Cobertura no COMPLETA ({', '.join(partial)}). Los resultados pueden "
                    "estar sesgados."
                )
            )
            return self.confirm("¿Continuar de todos modos?")
        return True

    def window_frame(self) -> tuple[cov.Window, pd.DataFrame]:
        win = cov.window(self.today())
        return win, load_window(self.bridge, win)

    # --- opción 3 ----------------------------------------------------------------------

    def ask_date(self, label: str) -> date | None:
        text = self.input(f"{label} (ej. 2026-03-01): ").strip()
        try:
            return date.fromisoformat(text)
        except ValueError:
            self.print(
                ui.error(
                    f"«{text}» no es una fecha válida. Escribe año-mes-día con cifras, "
                    "AAAA-MM-DD (ej. 2026-03-01)."
                )
            )
            return None

    def query_records(self) -> None:
        if not self.guard():
            return
        answer = self.input("Fuente (1 = ERA5 meteorología, 2 = CAMS PM2.5): ").strip()
        source = {"1": "ERA5", "2": "CAMS_GLOBAL"}.get(answer)
        if source is None:
            self.print(ui.error("Fuente no válida: escribe 1 (meteorología) o 2 (PM2.5)."))
            return
        first = self.ask_date("Desde, hora local")
        if first is None:
            return
        last = self.ask_date("Hasta, inclusive")
        if last is None:
            return
        start = datetime.combine(first, time.min, tzinfo=LOCAL_TZ)
        end = datetime.combine(last + timedelta(days=1), time.min, tzinfo=LOCAL_TZ)
        frame = self.bridge.export(source, start, end)
        columns = SOURCES[source].columns
        if frame.empty:
            self.print(ui.ok("0 registros en ese rango."))
            return
        table = pd.DataFrame(
            {
                "hora local": frame.index.tz_convert(LOCAL_TZ).strftime("%Y-%m-%d %H:%M"),
                "UTC": frame.index.strftime("%Y-%m-%d %H:%M"),
                **{plots.label(c): frame[c].to_numpy() for c in columns},
                "lote": frame["batch_id"].str[:8].to_numpy(),
            }
        )
        for page_start in range(0, len(table), PAGE_SIZE):
            page = table.iloc[page_start : page_start + PAGE_SIZE]
            self.print(ui.df_table(page, decimals=2))
            if page_start + PAGE_SIZE < len(table):
                more = self.input("Enter = siguiente página, q = terminar: ").strip().lower()
                if more == "q":
                    break
        nulls = int(frame[columns].isna().sum().sum())
        self.print(ui.ok(f"{len(frame)} registros, {nulls} valores nulos."))
        self.print(
            ui.meaning(
                "Cada fila es una hora. «—» significa que esa hora no tiene dato para la "
                "variable. «UTC» es la hora universal con la que se guardan los datos (en "
                "Medellín son 5 horas menos). «Lote» identifica la descarga que trajo el dato."
            )
        )

    # --- opción 4 ----------------------------------------------------------------------

    def show_statistics(self) -> None:
        if not self.guard():
            return
        win, frame = self.window_frame()
        stats = describe_variables(frame)
        stats.index = [plots.label(c) for c in stats.index]
        self.print(
            ui.df_table(
                stats,
                f"Resumen por variable ({win.start_local} → {win.end_local})",
                index_name="variable",
            )
        )
        bands = describe_bands(daily_bands(frame))
        self.print(
            ui.df_table(
                bands.rename(index=plots.label, level=0),
                "Medias por franja (mañana 07–09, tarde 13–15, noche 19–21 h)",
                index_name="variable · franja",
            )
        )
        pm = bands.loc["pm25_ug_m3", "media"]
        self.print(
            ui.meaning(
                "La media es el promedio; la mediana es el valor del medio y no la mueven los "
                "picos. El percentil 95 es el valor que solo superan el 5 % de las horas. Por "
                f"franjas, el PM2.5 medio es {pm['mañana']:.1f} µg/m³ por la mañana, "
                f"{pm['tarde']:.1f} por la tarde y {pm['noche']:.1f} por la noche "
                "(ojo: parte de la diferencia de la noche y la mañana viene de los empalmes "
                "del pronóstico de CAMS, no del aire)."
            )
        )

    # --- opción 5 ----------------------------------------------------------------------

    def run_regression(self) -> None:
        if not self.guard():
            return
        win, frame = self.window_frame()
        data, excluded = regression_dataset(frame)
        split = temporal_split(win)
        result = fit_and_evaluate(data, split)
        local = {k: pd.Timestamp(v).tz_convert(LOCAL_TZ) for k, v in vars(split).items()}
        self.print(Text("Modelo: PM2.5 a partir de temperatura, humedad y viento", style="bold"))
        self.print(
            f"Aprende con {local['train_start']:%Y-%m-%d} → {local['train_end']:%Y-%m-%d} "
            f"({result.n_train} horas) y se pone a prueba con {local['test_start']:%Y-%m-%d} → "
            f"{local['test_end']:%Y-%m-%d} ({result.n_test} horas), con 24 h de separación. "
            f"Horas sin todas las variables: {excluded}."
        )
        self.print(
            ui.df_table(
                result.metrics, "Qué tan bien predice (en la prueba)", index_name="", decimals=3
            )
        )
        coefficients = result.coefficients.assign(VIF=result.vif)
        coefficients.index = [plots.label(c) for c in coefficients.index]
        self.print(ui.df_table(coefficients, "Coeficientes", index_name="variable", decimals=3))
        self.print(
            f"{ui.TERMS['DW']}: {result.durbin_watson:.2f} (cerca de 2 = horas independientes; "
            "cerca de 0 = cada hora se parece mucho a la anterior)."
        )
        model_mae = result.metrics.loc["modelo", "MAE"]
        base_mae = result.metrics.loc["linea_base", "MAE"]
        gain = 100 * (base_mae - model_mae) / base_mae
        verdict = "mejora" if gain > 0 else "no mejora"
        self.print(
            ui.meaning(
                f"Con el clima de cada hora, el modelo se equivoca en promedio {model_mae:.1f} "
                f"µg/m³; predecir siempre la media se equivoca {base_mae:.1f}. Es decir, "
                f"{verdict} un {abs(gain):.0f} %. Describe una asociación dentro de los modelos "
                "ERA5 y CAMS, no una causa ni una medición real del aire de Medellín."
            )
        )

    # --- opción 6 ----------------------------------------------------------------------

    def predict_soon(self) -> None:
        self.print(ui.warn("La predicción estará disponible próximamente."))

    # --- opción 7 ----------------------------------------------------------------------

    def make_charts(self) -> None:
        if not self.guard():
            return
        answer = self.input("Salida (1 = ventana, 2 = guardar como PNG): ").strip()
        mode = {"1": "ventana", "2": "png"}.get(answer)
        if mode is None:
            self.print(ui.error("Opción de salida no válida: escribe 1 (ventana) o 2 (PNG)."))
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
        with self.progress() as bar:
            task = bar.add_task("Generando gráficas", total=len(figures))
            for name, build in figures.items():
                output = plots.save_or_show(build(), name, mode, self.outputs_dir)
                if output.notice:
                    self.print(ui.warn(output.notice))
                elif output.path:
                    self.print(ui.ok(f"Gráfica guardada: {output.path}"))
                bar.advance(task)
        self.print(ui.ok(f"{len(figures)} gráficas generadas."))
        self.print(
            ui.meaning(
                "Cada gráfica responde una pregunta: las series muestran el año completo, el "
                "perfil diurno el día típico, las franjas comparan mañana, tarde y noche, y las "
                "de residuos dónde falla el modelo. Los PNG llevan la fecha y hora en el nombre, "
                "así nunca se sobrescriben."
            )
        )
