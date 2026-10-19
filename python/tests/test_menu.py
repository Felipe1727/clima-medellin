"""Pruebas del menú con entradas programadas, el JAR real, una base temporal y la API falsa."""

from datetime import date
from pathlib import Path

import pytest
from fakes import FakeOpenMeteo

from clima_medellin import paths
from clima_medellin.bridge import JavaBridge
from clima_medellin.menu import Menu

TODAY = date(2026, 10, 18)


class Console:
    """Entradas programadas y salida capturada."""

    def __init__(self, *answers: str):
        self.answers = iter(answers)
        self.lines: list[str] = []

    def input(self, prompt: str) -> str:
        self.lines.append(prompt)
        return next(self.answers)

    def print(self, *parts) -> None:
        self.lines.append(" ".join(str(p) for p in parts))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def make_menu(tmp_path: Path, console: Console, *, fetch=None, jar=paths.JAR_PATH) -> Menu:
    bridge = JavaBridge(
        tmp_path / "data" / "test.odb",
        jar=jar,
        staging_dir=tmp_path / "staging",
        exchange_dir=tmp_path / "exchange",
    )
    return Menu(
        bridge,
        fetch=fetch or FakeOpenMeteo(TODAY),
        today=TODAY,
        outputs_dir=tmp_path / "outputs",
        input_fn=console.input,
        print_fn=console.print,
    )


def test_end_to_end_from_an_empty_database(tmp_path):
    console = Console(
        "1",  # cobertura con la base vacía
        "2",
        "s",  # actualizar y confirmar
        "1",  # cobertura tras la carga
        "3",
        "1",
        "2026-03-01",
        "2026-03-01",
        "",  # consultar un día de ERA5 (2 páginas)
        "4",  # estadísticas
        "5",  # regresión
        "6",
        "2",  # gráficas en PNG
        "7",
    )
    make_menu(tmp_path, console).run()
    text = console.text

    assert "Ubicación: MED-CENTRO · Ventana: 2025-10-18 → 2026-10-18" in text
    assert text.count("estado SIN_DATOS") == 2
    assert "Se pedirán 2 intervalos" in text
    assert "[…] Descargando ERA5 2025-10-18 → 2026-10-13 (1/2)" in text
    assert text.count("[OK] Lote importado:") == 2
    assert text.count("estado COMPLETA") >= 2
    assert "[OK] 24 registros, 0 valores nulos." in text
    assert "2026-03-01 00:00" in text  # hora local de la consulta
    assert "Medias por franja" in text and "mañana" in text
    assert "linea_base" in text and "Durbin-Watson" in text
    assert "[OK] 13 gráficas generadas." in text
    assert len(list((tmp_path / "outputs").glob("*.png"))) == 13
    assert "[ERROR]" not in text
    assert text.endswith("Hasta pronto.")


def test_invalid_option_shows_an_error(tmp_path):
    console = Console("9", "7")
    make_menu(tmp_path, console).run()
    assert "[ERROR] Opción no válida: '9'" in console.text
    assert console.text.count("1) Verificar cobertura") == 2


def test_empty_database_suggests_option_2(tmp_path):
    console = Console("4", "7")
    make_menu(tmp_path, console).run()
    assert "Ejecuta primero la opción 2" in console.text


def test_cancelled_update_downloads_nothing(tmp_path):
    fake = FakeOpenMeteo(TODAY)
    console = Console("2", "", "7")
    make_menu(tmp_path, console, fetch=fake).run()
    assert "Actualización cancelada." in console.text
    assert fake.calls == []


def test_up_to_date_database_has_nothing_to_download(tmp_path):
    console = Console("2", "s", "2", "7")
    make_menu(tmp_path, console).run()
    assert "No hay nada que descargar" in console.text
    assert console.text.count("¿Continuar?") == 1


def test_partial_coverage_asks_before_continuing(tmp_path):
    fake = FakeOpenMeteo(TODAY, skip={"ERA5": {date(2026, 3, 10)}})
    console = Console("2", "s", "4", "n", "7")
    make_menu(tmp_path, console, fetch=fake).run()
    assert "[AVISO] Cobertura no COMPLETA (ERA5 PARCIAL)" in console.text
    assert "Medias por franja" not in console.text


def test_bridge_error_returns_to_the_menu(tmp_path):
    console = Console("1", "7")
    make_menu(tmp_path, console, jar=tmp_path / "no-existe.jar").run()
    assert "[ERROR] No se encuentra el JAR" in console.text
    assert console.text.endswith("Hasta pronto.")


@pytest.mark.parametrize("answer", ["x", "3"])
def test_invalid_chart_mode(tmp_path, answer):
    console = Console("2", "s", "6", answer, "7")
    make_menu(tmp_path, console).run()
    assert "[ERROR] Opción de salida no válida." in console.text
