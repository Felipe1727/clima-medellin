"""Pruebas de las gráficas con el backend Agg y datos de las muestras."""

import json
from datetime import UTC, date, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from clima_medellin import plots
from clima_medellin.bands import daily_bands
from clima_medellin.coverage import window
from clima_medellin.dataset import combine
from clima_medellin.normalize import normalize
from clima_medellin.regression import fit_and_evaluate, regression_dataset
from clima_medellin.split import temporal_split

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
WIN = window(date(2026, 10, 18))
SPLIT = temporal_split(WIN)


@pytest.fixture(scope="module")
def frame() -> pd.DataFrame:
    def load(name):
        return json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))

    weather = normalize("ERA5", load("era5_year.json"), datetime(2026, 10, 14, tzinfo=UTC))
    air = normalize("CAMS_GLOBAL", load("cams_pm25_year.json"), WIN.end_utc)
    joined = combine(weather.frame, air.frame)
    return joined[(joined.index >= WIN.start_utc) & (joined.index < WIN.end_utc)]


@pytest.fixture(scope="module")
def result(frame):
    data, _ = regression_dataset(frame)
    return fit_and_evaluate(data, SPLIT)


def all_texts(fig) -> list[str]:
    texts = [t.get_text() for t in fig.texts]
    if fig._suptitle is not None:
        texts.append(fig._suptitle.get_text())
    return texts


def assert_annotated(fig, unit_axes: int = 1):
    texts = all_texts(fig)
    assert plots.ATTRIBUTION in texts
    assert any(t.startswith("Periodo: ") for t in texts)
    assert fig._suptitle is not None and fig._suptitle.get_text()
    labelled = [
        ax.get_ylabel() for ax in fig.axes if "(" in ax.get_ylabel() or "(" in ax.get_xlabel()
    ]
    assert len(labelled) >= unit_axes
    plt.close(fig)


def test_time_series_is_annotated(frame):
    fig = plots.time_series(frame, "pm25_ug_m3", WIN.start_utc, WIN.end_utc)
    assert fig.axes[0].get_ylabel() == "PM2.5 (µg/m³)"
    assert_annotated(fig)


def test_time_series_does_not_join_a_gap(frame):
    holed = frame.drop(index=frame.index[100:105])
    fig = plots.time_series(holed, "temperature_2m_c", WIN.start_utc, WIN.end_utc)
    line = fig.axes[0].lines[0]
    y = np.asarray(line.get_ydata(), dtype=float)
    assert np.isnan(y[100:105]).all()
    assert not np.isnan(y[99]) and not np.isnan(y[105])
    plt.close(fig)


def test_diurnal_profile(frame):
    fig = plots.diurnal_profile(frame, SPLIT)
    assert len(fig.axes) == 4
    assert all(ax.get_xlabel() == "Hora local" for ax in fig.axes)
    assert_annotated(fig, unit_axes=4)


def test_band_boxplots_show_valid_days(frame):
    fig = plots.band_boxplots(daily_bands(frame), WIN.start_utc, WIN.end_utc)
    ticks = [t.get_text() for t in fig.axes[0].get_xticklabels()]
    assert all("días" in t for t in ticks)
    assert_annotated(fig, unit_axes=4)


def test_scatter_and_correlation(frame):
    data, _ = regression_dataset(frame)
    assert_annotated(plots.scatter_predictors(data, SPLIT), unit_axes=3)
    fig = plots.correlation_matrix(data, SPLIT)
    texts = all_texts(fig)
    assert plots.ATTRIBUTION in texts
    plt.close(fig)


def test_coverage_map_states(frame):
    existing = frame[["pm25_ug_m3"]].notna()
    existing = existing.iloc[:-48]
    existing.iloc[0, 0] = False
    fig = plots.coverage_map(existing, "CAMS_GLOBAL", WIN.start_utc, WIN.end_utc)
    image = fig.axes[0].images[0].get_array()
    values = set(np.unique(np.asarray(image)))
    assert values == {0, 1, 2}  # ausente, parcial y presente
    assert [t.get_text() for t in fig.axes[0].get_legend().get_texts()][0] == "presente"
    plt.close(fig)


def test_seam_diagnostic_highlights_00_and_12(frame):
    fig = plots.seam_diagnostic(frame["pm25_ug_m3"], WIN.start_utc, WIN.end_utc)
    bars = fig.axes[0].patches
    assert len(bars) == 24
    highlighted = [
        i for i, b in enumerate(bars) if b.get_facecolor()[:3] != bars[1].get_facecolor()[:3]
    ]
    assert highlighted == [0, 12]
    labels = [t.get_text() for t in fig.axes[0].texts]
    assert len(labels) == 2
    assert_annotated(fig)


def test_model_charts_use_only_the_test_period(result):
    fig = plots.actual_vs_predicted(result)
    line = fig.axes[1].lines[0]
    first = pd.Timestamp(line.get_xdata()[0])
    assert first >= pd.Timestamp(SPLIT.test_start).tz_convert("America/Bogota")
    assert [t.get_text() for t in fig.axes[1].get_legend().get_texts()] == ["real", "predicho"]
    assert any("periodo de prueba" in t for t in all_texts(fig))
    assert_annotated(fig, unit_axes=2)
    fig = plots.residuals(result)
    assert len(fig.axes) == 3
    assert_annotated(fig, unit_axes=2)


def test_png_is_written_with_the_naming_pattern(tmp_path, frame):
    fig = plots.time_series(frame, "pm25_ug_m3", WIN.start_utc, WIN.end_utc)
    out = plots.save_or_show(fig, "perfil_diurno", "png", tmp_path)
    assert out.path.exists() and out.notice is None
    assert out.path.name.startswith("perfil_diurno_")
    stamp = out.path.stem.removeprefix("perfil_diurno_")
    datetime.strptime(stamp, "%Y%m%d-%H%M%S")


def test_existing_png_is_not_overwritten(tmp_path, frame):
    paths_written = []
    for _ in range(2):
        fig = plots.time_series(frame, "pm25_ug_m3", WIN.start_utc, WIN.end_utc)
        paths_written.append(plots.save_or_show(fig, "serie", "png", tmp_path).path)
    assert paths_written[0] != paths_written[1]
    assert all(p.exists() for p in paths_written)


def test_window_without_display_falls_back_to_png(tmp_path, frame):
    assert not plots.has_display()  # backend Agg
    fig = plots.time_series(frame, "pm25_ug_m3", WIN.start_utc, WIN.end_utc)
    out = plots.save_or_show(fig, "serie", "ventana", tmp_path)
    assert out.path is not None and out.path.exists()
    assert "No hay pantalla" in out.notice and str(out.path) in out.notice


def test_hour_effects_chart(frame):
    from clima_medellin.calendar_models import fit_calendar_models

    models = fit_calendar_models(frame, SPLIT)
    fig = plots.hour_effects(models, WIN.start_utc, WIN.end_utc)
    assert len(fig.axes) == 3
    assert all(len(ax.patches) == 24 for ax in fig.axes)
    assert fig.axes[0].get_ylabel() == "Diferencia con la medianoche (°C)"
    assert_annotated(fig, unit_axes=3)


def test_prediction_chart_with_real_values(frame):
    from clima_medellin.calendar_models import fit_calendar_models, predict, request_hours

    models = fit_calendar_models(frame, SPLIT)
    hours = request_hours("2026-03-01", "2026-03-03", WIN, date(2026, 10, 18))
    fig = plots.prediction_chart(predict(models, hours, frame), models)
    assert len(fig.axes) == 3
    for ax in fig.axes:
        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        assert labels[1:] == ["valor típico", "real"] and labels[0].startswith("± error típico")
        assert len(ax.collections) == 1  # la banda
    assert_annotated(fig, unit_axes=3)
