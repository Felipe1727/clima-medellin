"""Pruebas del menú con entradas programadas, el JAR real, una base temporal y la API falsa."""

import io
import os
import subprocess
from datetime import date
from pathlib import Path

import pytest
from fakes import FakeOpenMeteo
from rich.console import Console

from clima_medellin import paths, ui
from clima_medellin.bridge import JavaBridge
from clima_medellin.menu import Menu

TODAY = date(2026, 10, 18)


class Session:
    """Entradas programadas y una consola de rich que graba el texto sin colores."""

    def __init__(self, *answers: str):
        self.answers = iter(answers)
        self.prompts: list[str] = []
        self.console = Console(file=io.StringIO(), width=140, color_system=None, record=True)

    def input(self, prompt: str) -> str:
        self.prompts.append(prompt)
        self.console.print(prompt)
        return next(self.answers)

    @property
    def text(self) -> str:
        return self.console.export_text(clear=False)


def make_menu(tmp_path: Path, session: Session, *, fetch=None, jar=paths.JAR_PATH) -> Menu:
    bridge = JavaBridge(
        tmp_path / "data" / "test.odb",
        jar=jar,
        staging_dir=tmp_path / "staging",
        exchange_dir=tmp_path / "exchange",
    )
    return Menu(
        bridge,
        console=session.console,
        fetch=fetch or FakeOpenMeteo(TODAY),
        today=TODAY,
        outputs_dir=tmp_path / "outputs",
        input_fn=session.input,
    )


def test_end_to_end_from_an_empty_database(tmp_path):
    session = Session(
        "1",  # cobertura con la base vacía
        "2",
        "s",  # descargar y confirmar
        "1",  # cobertura tras la carga
        "3",
        "1",
        "2026-03-01",
        "2026-03-01",
        "",  # consultar un día de ERA5 (2 páginas)
        "4",  # resumen estadístico
        "5",  # evaluación del modelo
        "7",
        "2",  # gráficas en PNG
        "0",
    )
    make_menu(tmp_path, session).run()
    text = session.text

    assert "Datos del último año: 2025-10-18 → 2026-10-18" in text
    assert "Base de datos: vacía" in text and "Base de datos: al día" in text
    assert text.count("SIN_DATOS (sin datos)") == 2
    assert "Se pedirán 2 intervalos" in text
    assert "[…] Descargando ERA5 2025-10-18 → 2026-10-13 (1/2)" in text
    assert text.count("[OK] Lote importado:") == 2
    assert text.count("COMPLETA (completa)") >= 4
    assert "[OK] 24 registros, 0 valores nulos." in text
    assert "2026-03-01 00:00" in text
    assert "Medias por franja" in text and "mañana" in text
    assert "error típico (MAE)" in text and "línea base (predecir siempre la media)" in text
    assert "dependencia entre horas seguidas (Durbin-Watson)" in text
    assert "[OK] 13 gráficas generadas." in text
    assert len(list((tmp_path / "outputs").glob("*.png"))) == 13
    assert text.count("Qué significa") == 7  # opciones 1 (×2), 2, 3, 4, 5 y 7
    assert "[ERROR]" not in text
    assert text.rstrip().endswith("Hasta pronto.")


def test_menu_is_grouped_and_zero_exits(tmp_path):
    session = Session("0")
    make_menu(tmp_path, session).run()
    text = session.text
    for group in ("DATOS", "ANÁLISIS", "PREDICCIONES"):
        assert group in text
    assert "7  Generar gráficas" in text and "0  Salir" in text
    assert "Base de datos: vacía · no hay datos: empieza por la opción 2" in text


def test_invalid_option_shows_an_error(tmp_path):
    session = Session("9", "0")
    make_menu(tmp_path, session).run()
    assert "[ERROR] Opción no válida: '9'" in session.text
    assert session.text.count("1  Ver qué datos hay guardados") == 2


def test_prediction_option_is_coming_soon(tmp_path):
    session = Session("6", "0")
    make_menu(tmp_path, session).run()
    assert "estará disponible próximamente" in session.text


def test_empty_database_suggests_option_2(tmp_path):
    session = Session("4", "0")
    make_menu(tmp_path, session).run()
    assert "Ejecuta primero la opción 2" in session.text


def test_cancelled_update_downloads_nothing(tmp_path):
    fake = FakeOpenMeteo(TODAY)
    session = Session("2", "", "0")
    make_menu(tmp_path, session, fetch=fake).run()
    assert "Actualización cancelada." in session.text
    assert fake.calls == []


def test_up_to_date_database_has_nothing_to_download(tmp_path):
    session = Session("2", "s", "2", "0")
    make_menu(tmp_path, session).run()
    assert "No hay nada que descargar" in session.text
    assert sum("¿Continuar?" in p for p in session.prompts) == 1


def test_invalid_date_is_explained(tmp_path):
    session = Session("2", "s", "3", "1", "03/01/2026", "0")
    make_menu(tmp_path, session).run()
    assert "«03/01/2026» no es una fecha válida" in session.text
    assert "AAAA-MM-DD (ej. 2026-03-01)" in session.text


def test_partial_coverage_asks_before_continuing(tmp_path):
    fake = FakeOpenMeteo(TODAY, skip={"ERA5": {date(2026, 3, 10)}})
    session = Session("2", "s", "4", "n", "0")
    make_menu(tmp_path, session, fetch=fake).run()
    assert "[AVISO] Cobertura no COMPLETA (ERA5 PARCIAL)" in session.text
    assert "Base de datos: incompleta" in session.text
    assert "Medias por franja" not in session.text


def test_bridge_error_returns_to_the_menu(tmp_path):
    session = Session("1", "0")
    make_menu(tmp_path, session, jar=tmp_path / "no-existe.jar").run()
    assert "[ERROR] No se encuentra el JAR" in session.text
    assert "Base de datos: desconocido" in session.text
    assert session.text.rstrip().endswith("Hasta pronto.")


@pytest.mark.parametrize("answer", ["x", "3"])
def test_invalid_chart_mode(tmp_path, answer):
    session = Session("2", "s", "7", answer, "0")
    make_menu(tmp_path, session).run()
    assert "[ERROR] Opción de salida no válida" in session.text


def test_no_color_and_redirected_output_have_no_color_codes():
    terminal = Console(file=io.StringIO(), force_terminal=True, color_system="truecolor")
    terminal.print(ui.state_text("COMPLETA"))
    assert "\x1b[" in terminal.file.getvalue()  # control: en una terminal sí hay color

    env = {**os.environ, "NO_COLOR": "1"}
    script = (
        "import io; from rich.console import Console; from clima_medellin import ui;"
        "c = Console(file=io.StringIO(), force_terminal=True); c.print(ui.state_text('PARCIAL'));"
        "print(repr(c.file.getvalue()))"
    )
    output = subprocess.run(
        ["python", "-c", script], env=env, capture_output=True, text=True, check=True
    ).stdout
    assert "PARCIAL (incompleta)" in output
    assert "[33m" not in output and "38;" not in output  # sin códigos de color

    redirected = Console(file=io.StringIO())  # un archivo no es una terminal
    redirected.print(ui.state_text("SIN_DATOS"), ui.error("x"))
    assert "\x1b" not in redirected.file.getvalue()
