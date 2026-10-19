"""Pruebas de humo del comando ``clima-medellin``."""

import shutil
import subprocess

import pytest

from clima_medellin import __version__
from clima_medellin.cli import main


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"clima-medellin {__version__}"


def test_no_options_prints_menu_notice(capsys):
    assert main([]) == 0
    assert "aún no está disponible" in capsys.readouterr().out


def test_console_script_is_installed():
    executable = shutil.which("clima-medellin")
    assert executable is not None
    result = subprocess.run([executable, "--version"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert result.stdout.strip() == f"clima-medellin {__version__}"
