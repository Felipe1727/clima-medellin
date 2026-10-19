"""Pruebas del puente con el JAR real contra una base temporal.

El JAR lo construye el comando de pruebas (``mvn -q verify``) antes de ejecutar pytest.
"""

import copy
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from clima_medellin import paths
from clima_medellin.bridge import BridgeError, JavaBridge
from clima_medellin.config import ERA5
from clima_medellin.normalize import normalize

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
WEATHER_COLUMNS = ["temperature_2m_c", "relative_humidity_2m_pct", "wind_speed_10m_ms"]


@pytest.fixture
def bridge(tmp_path) -> JavaBridge:
    assert paths.JAR_PATH.is_file(), (
        f"Falta {paths.JAR_PATH}: ejecuta «cd java && mvn -q -DskipTests package»"
    )
    return JavaBridge(
        tmp_path / "data" / "test.odb",
        staging_dir=tmp_path / "staging",
        exchange_dir=tmp_path / "exchange",
    )


@pytest.fixture(scope="module")
def era5_week() -> pd.DataFrame:
    """Una semana normalizada de la muestra anual de ERA5, con un nulo parcial."""
    payload = copy.deepcopy(json.loads((SAMPLES_DIR / "era5_year.json").read_text("utf-8")))
    payload["hourly"]["wind_speed_10m"][5] = None
    today = date.fromisoformat(
        json.loads((SAMPLES_DIR / "manifest.json").read_text("utf-8"))["today_local"]
    )
    end = datetime.combine(today - timedelta(days=4), datetime.min.time(), tzinfo=UTC)
    frame = normalize("ERA5", payload, end).frame
    return frame.iloc[: 7 * 24]


def import_week(bridge: JavaBridge, frame: pd.DataFrame) -> dict:
    return bridge.import_frame(
        "ERA5",
        frame,
        requested_start=frame.index[0].to_pydatetime(),
        requested_end=frame.index[-1].to_pydatetime() + timedelta(hours=1),
        endpoint=ERA5.url,
        params=ERA5.fixed_params,
    )


def test_round_trip_is_identical(bridge, era5_week):
    response = import_week(bridge, era5_week)
    assert response["ok"] and response["inserted"] == len(era5_week)

    exported = bridge.export(
        "ERA5", era5_week.index[0], era5_week.index[-1] + pd.Timedelta(hours=1)
    )

    pd.testing.assert_frame_equal(exported[WEATHER_COLUMNS], era5_week[WEATHER_COLUMNS])
    assert exported["wind_speed_10m_ms"].isna().sum() == 1
    assert (exported["batch_id"] == response["batch_id"]).all()


def test_staging_file_is_deleted_after_success(bridge, era5_week):
    import_week(bridge, era5_week)
    assert list(bridge.staging_dir.glob("*.jsonl")) == []


def test_second_import_inserts_nothing(bridge, era5_week):
    import_week(bridge, era5_week)
    again = import_week(bridge, era5_week)
    assert again["inserted"] == 0
    assert again["duplicates"] == len(era5_week)


def test_corrupt_line_gives_spanish_message_and_keeps_staging(bridge, era5_week, monkeypatch):
    def corrupt_writer(frame, source, location_code, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"location_code":"MED-CENTRO"}\n{roto\n', encoding="utf-8")
        return 2

    monkeypatch.setattr("clima_medellin.bridge.write_frame", corrupt_writer)
    with pytest.raises(BridgeError) as exc:
        import_week(bridge, era5_week)
    error = exc.value
    assert error.exit_code == 2 and error.error_type == "DATA"
    assert "datos inválidos" in str(error) and "Línea 1" in str(error)
    assert error.staging_file is not None and error.staging_file.exists()
    assert str(error.staging_file) in str(error)


def test_unknown_subcommand_is_a_usage_error(bridge):
    with pytest.raises(BridgeError) as exc:
        bridge.run("borrar-todo")
    assert exc.value.exit_code == 1
    assert "Error de uso" in str(exc.value)


def test_coverage_lists_stored_timestamps_and_non_null_variables(bridge, era5_week):
    import_week(bridge, era5_week)
    snapshot = bridge.coverage("ERA5")
    assert snapshot.summary["count"] == len(era5_week)
    assert snapshot.summary["non_null"]["wind_speed_10m_ms"] == len(era5_week) - 1
    assert list(snapshot.existing.columns) == WEATHER_COLUMNS
    assert snapshot.existing.index.equals(era5_week.index)
    assert snapshot.existing["wind_speed_10m_ms"].sum() == len(era5_week) - 1
    assert (bridge.exchange_dir / "coverage-ERA5.jsonl").exists()


def test_coverage_of_empty_database(bridge):
    snapshot = bridge.coverage("CAMS_GLOBAL")
    assert snapshot.summary["count"] == 0
    assert snapshot.existing.empty


def test_verbose_mode_forwards_java_stderr(tmp_path, capsys):
    quiet = JavaBridge(tmp_path / "q.odb", exchange_dir=tmp_path / "exchange")
    quiet.coverage("ERA5")
    assert capsys.readouterr().err == ""

    loud = JavaBridge(tmp_path / "v.odb", exchange_dir=tmp_path / "exchange", verbose=True)
    loud.coverage("ERA5")
    assert "[coverage]" in capsys.readouterr().err
