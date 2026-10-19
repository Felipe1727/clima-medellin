"""Pruebas del comando ``clima-medellin``."""

import shutil
import subprocess

import pytest

from clima_medellin import __version__, cli


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"clima-medellin {__version__}"


class FakeMenu:
    instances: list[FakeMenu] = []

    def __init__(self, bridge):
        self.bridge = bridge
        FakeMenu.instances.append(self)

    def run(self):
        print("Hasta pronto.")


def test_no_options_opens_the_menu(monkeypatch, capsys):
    monkeypatch.setattr(cli, "Menu", FakeMenu)
    assert cli.main([]) == 0
    assert "Hasta pronto." in capsys.readouterr().out
    assert FakeMenu.instances[-1].bridge.verbose is False


def test_verbose_flag_enables_java_logs(monkeypatch):
    monkeypatch.setattr(cli, "Menu", FakeMenu)
    assert cli.main(["--verbose"]) == 0
    assert FakeMenu.instances[-1].bridge.verbose is True


def test_console_script_is_installed():
    executable = shutil.which("clima-medellin")
    assert executable is not None
    result = subprocess.run([executable, "--version"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert result.stdout.strip() == f"clima-medellin {__version__}"


def test_console_script_exits_cleanly_on_option_7():
    executable = shutil.which("clima-medellin")
    result = subprocess.run(
        [executable], input="7\n", capture_output=True, text=True, check=False, timeout=60
    )
    assert result.returncode == 0
    assert "CLIMA MEDELLÍN" in result.stdout and "Hasta pronto." in result.stdout
