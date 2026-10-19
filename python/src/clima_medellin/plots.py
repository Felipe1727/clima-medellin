"""Gráficas con Matplotlib: una función por gráfica, con título, unidades, periodo y fuente."""

import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from clima_medellin import paths
from clima_medellin.bands import BANDS, to_local
from clima_medellin.config import LOCAL_TZ
from clima_medellin.regression import RegressionResult
from clima_medellin.split import Split

ATTRIBUTION = "Datos: Open-Meteo.com (ERA5, CAMS)"

# Paleta validada (guía de visualización): una serie → SERIES_1; dos → SERIES_1 y SERIES_2.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
DIVERGING_LOW, DIVERGING_MID, DIVERGING_HIGH = "#2a78d6", "#f0efec", "#e34948"

NAMES = {
    "temperature_2m_c": "Temperatura a 2 m",
    "relative_humidity_2m_pct": "Humedad relativa a 2 m",
    "wind_speed_10m_ms": "Viento a 10 m",
    "pm25_ug_m3": "PM2.5",
}
UNITS = {
    "temperature_2m_c": "°C",
    "relative_humidity_2m_pct": "%",
    "wind_speed_10m_ms": "m/s",
    "pm25_ug_m3": "µg/m³",
}


def label(column: str) -> str:
    """Rótulo de eje con la unidad entre paréntesis, p. ej. «PM2.5 (µg/m³)»."""
    return f"{NAMES[column]} ({UNITS[column]})"


def _style() -> dict:
    return {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_SECONDARY,
        "axes.titlecolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linestyle": "-",
        "grid.linewidth": 0.6,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "text.color": INK,
        "font.family": "sans-serif",
        "font.size": 9,
        "legend.frameon": False,
    }


def _figure(nrows: int = 1, ncols: int = 1, size=(10, 4.5)) -> tuple[Figure, np.ndarray]:
    with plt.rc_context(_style()):
        fig, axes = plt.subplots(nrows, ncols, figsize=size, squeeze=False)
    for ax in axes.flat:
        ax.set_axisbelow(True)
    return fig, axes


def _finish(fig: Figure, title: str, period: str) -> Figure:
    """Título, periodo y atribución: la anotación obligatoria de toda gráfica."""
    # Posiciones en pulgadas desde el borde superior, para que no se solapen en
    # figuras bajas.
    height = fig.get_figheight()
    fig.suptitle(
        title,
        x=0.01,
        y=1 - 0.12 / height,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )
    fig.text(0.01, 1 - 0.42 / height, period, ha="left", va="top", fontsize=9, color=INK_SECONDARY)
    fig.text(0.99, 0.01, ATTRIBUTION, ha="right", fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.25 / height, 1, 1 - 0.7 / height))
    return fig


def period_text(start: datetime, end: datetime) -> str:
    """«Periodo: 2025-10-18 → 2026-10-18 (hora de Medellín)» a partir de extremos UTC."""
    first = pd.Timestamp(start).tz_convert(LOCAL_TZ).strftime("%Y-%m-%d")
    last = pd.Timestamp(end).tz_convert(LOCAL_TZ).strftime("%Y-%m-%d")
    return f"Periodo: {first} → {last} (hora de Medellín)"


# --- Gráficas de los datos -------------------------------------------------------------


def time_series(frame: pd.DataFrame, column: str, start: datetime, end: datetime) -> Figure:
    """Serie horaria de una variable; las horas sin dato cortan la línea."""
    hours = pd.date_range(
        pd.Timestamp(start).ceil("h"), pd.Timestamp(end), freq="h", inclusive="left"
    )
    # Reindexar a la rejilla horaria completa: las horas sin fila pasan a NaN y
    # Matplotlib no une los puntos a ambos lados de un NaN.
    series = frame[column].reindex(hours).tz_convert(LOCAL_TZ)
    fig, axes = _figure()
    ax = axes[0, 0]
    ax.plot(series.index, series.to_numpy(), color=SERIES_1, linewidth=1.0)
    ax.set_xlabel("Fecha (hora de Medellín)")
    ax.set_ylabel(label(column))
    gaps = int(series.isna().sum())
    ax.set_title(
        f"{gaps} horas sin dato (cortes de la línea)", loc="left", fontsize=9, color=INK_MUTED
    )
    return _finish(fig, f"Serie temporal: {NAMES[column]}", period_text(start, end))


def diurnal_profile(frame: pd.DataFrame, split: Split) -> Figure:
    """Media ± desviación por hora local (entrenamiento) con las franjas sombreadas."""
    local = to_local(split.train(frame))
    grouped = local.groupby(local.index.hour)
    mean, std, count = grouped.mean(), grouped.std(), grouped.count()
    fig, axes = _figure(2, 2, size=(10, 6.5))
    for ax, column in zip(axes.flat, frame.columns, strict=True):
        for band, hours in BANDS.items():
            ax.axvspan(hours[0] - 0.5, hours[-1] + 0.5, color=GRID, alpha=0.7, linewidth=0)
            ax.text(
                hours[1],
                1.0,
                band,
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=8,
                color=INK_SECONDARY,
            )
        m, s = mean[column].reindex(range(24)), std[column].reindex(range(24))
        ax.fill_between(range(24), m - s, m + s, color=SERIES_1, alpha=0.15, linewidth=0)
        ax.plot(range(24), m, color=SERIES_1, linewidth=2)
        ax.set_xticks(range(0, 24, 3))
        ax.set_xlim(-0.5, 23.5)
        ax.set_xlabel("Hora local")
        ax.set_ylabel(label(column))
        ax.set_title(
            f"n = {int(count[column].min())}–{int(count[column].max())} por hora",
            loc="left",
            fontsize=8,
            color=INK_MUTED,
            pad=14,
        )
    period = period_text(split.train_start, split.train_end) + " · solo entrenamiento"
    return _finish(fig, "Perfil diurno (media ± desviación estándar)", period)


def band_boxplots(bands: pd.DataFrame, start: datetime, end: datetime) -> Figure:
    """Diagramas de caja de los valores de cada franja, con los días válidos."""
    columns = list(dict.fromkeys(bands.columns.get_level_values(0)))
    fig, axes = _figure(2, 2, size=(10, 6.5))
    for ax, column in zip(axes.flat, columns, strict=False):
        data = [bands[(column, band)].dropna().to_numpy() for band in BANDS]
        ax.boxplot(
            data,
            tick_labels=[f"{band}\n{len(d)} días" for band, d in zip(BANDS, data, strict=True)],
            widths=0.5,
            patch_artist=True,
            boxprops={"facecolor": SURFACE, "edgecolor": SERIES_1, "linewidth": 1.5},
            medianprops={"color": SERIES_1, "linewidth": 2},
            whiskerprops={"color": SERIES_1},
            capprops={"color": SERIES_1},
            flierprops={
                "markerfacecolor": SERIES_1,
                "markeredgecolor": SURFACE,
                "markersize": 4,
                "alpha": 0.5,
            },
        )
        ax.set_xlabel("Franja (hora local)")
        ax.set_ylabel(label(column))
    return _finish(fig, "Comparación por franjas", period_text(start, end))


def scatter_predictors(data: pd.DataFrame, split: Split) -> Figure:
    """PM2.5 frente a cada predictora, con los datos de entrenamiento."""
    train = split.train(data)
    fig, axes = _figure(1, 3, size=(12, 4.5))
    for ax, column in zip(
        axes.flat,
        ["temperature_2m_c", "relative_humidity_2m_pct", "wind_speed_10m_ms"],
        strict=True,
    ):
        ax.scatter(
            train[column], train["pm25_ug_m3"], s=6, color=SERIES_1, alpha=0.25, linewidths=0
        )
        ax.set_xlabel(label(column))
        ax.set_ylabel(label("pm25_ug_m3"))
    period = period_text(split.train_start, split.train_end) + " · solo entrenamiento"
    return _finish(fig, "PM2.5 frente a cada predictora", period)


def correlation_matrix(data: pd.DataFrame, split: Split) -> Figure:
    """Correlación de Pearson entre las cuatro variables (entrenamiento)."""
    corr = split.train(data).corr()
    cmap = LinearSegmentedColormap.from_list(
        "divergente", [DIVERGING_LOW, DIVERGING_MID, DIVERGING_HIGH]
    )
    fig, axes = _figure(size=(7, 6))
    ax = axes[0, 0]
    ax.grid(False)
    image = ax.imshow(corr.to_numpy(), cmap=cmap, vmin=-1, vmax=1)
    names = [NAMES[c] for c in corr.columns]
    ax.set_xticks(range(len(names)), names, rotation=20, ha="right")
    ax.set_yticks(range(len(names)), names)
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(j, i, f"{corr.iat[i, j]:.2f}", ha="center", va="center", color=INK)
    fig.colorbar(image, ax=ax, label="Coeficiente de correlación (sin unidad)")
    period = period_text(split.train_start, split.train_end) + " · solo entrenamiento"
    return _finish(fig, "Matriz de correlación", period)


def coverage_map(existing: pd.DataFrame, source: str, start: datetime, end: datetime) -> Figure:
    """Matriz días × horas locales: presente, parcial (alguna variable nula) o ausente."""
    hours = pd.date_range(
        pd.Timestamp(start).ceil("h"), pd.Timestamp(end), freq="h", inclusive="left"
    )
    exists = hours.isin(existing.index)
    present = exists & existing.reindex(hours, fill_value=False).all(axis=1).to_numpy()
    partial = exists & ~present
    state = pd.Series(0, index=hours)  # 0 = ausente
    state[partial] = 1
    state[present] = 2
    local = state.tz_convert(LOCAL_TZ)
    grid = (
        pd.DataFrame({"dia": local.index.date, "hora": local.index.hour, "estado": local})
        .pivot_table(index="dia", columns="hora", values="estado", aggfunc="max")
        .reindex(columns=range(24))
        .fillna(0)
    )
    fig, axes = _figure(size=(10, 6))
    ax = axes[0, 0]
    ax.grid(False)
    cmap = ListedColormap([GRID, SERIES_2, SERIES_1])
    ax.imshow(grid.to_numpy().T, aspect="auto", cmap=cmap, vmin=0, vmax=2, interpolation="nearest")
    ticks = np.linspace(0, len(grid) - 1, min(8, len(grid))).astype(int)
    ax.set_xticks(ticks, [grid.index[t].strftime("%Y-%m-%d") for t in ticks], rotation=20)
    ax.set_yticks(range(0, 24, 3))
    ax.set_xlabel("Día (hora de Medellín)")
    ax.set_ylabel("Hora local")
    ax.legend(
        handles=[
            Patch(color=SERIES_1, label="presente"),
            Patch(color=SERIES_2, label="parcial (alguna variable nula)"),
            Patch(color=GRID, label="ausente"),
        ],
        loc="upper left",
        bbox_to_anchor=(0, -0.18),
        ncol=3,
        frameon=False,
    )
    return _finish(fig, f"Mapa de cobertura: {source}", period_text(start, end))


def seam_diagnostic(pm25: pd.Series, start: datetime, end: datetime) -> Figure:
    """Salto absoluto medio de PM2.5 hacia cada hora UTC: revela los empalmes de 00 y 12 UTC."""
    hours = pd.date_range(
        pd.Timestamp(start).ceil("h"), pd.Timestamp(end), freq="h", inclusive="left"
    )
    series = pm25.reindex(hours)
    jumps = series.diff().abs()  # solo entre horas consecutivas con dato
    by_hour = jumps.groupby(jumps.index.hour).mean().reindex(range(24))
    colors = [SERIES_2 if h in (0, 12) else SERIES_1 for h in range(24)]
    fig, axes = _figure()
    ax = axes[0, 0]
    ax.bar(range(24), by_hour.to_numpy(), color=colors, width=0.8)
    for hour in (0, 12):
        ax.annotate(
            f"{by_hour[hour]:.1f}",
            (hour, by_hour[hour]),
            ha="center",
            va="bottom",
            xytext=(0, 2),
            textcoords="offset points",
            color=INK,
        )
    ax.set_xticks(range(24))
    ax.set_xlabel("Hora UTC de llegada (00 UTC = 19 h y 12 UTC = 7 h en Medellín)")
    ax.set_ylabel("Salto absoluto medio de PM2.5 (µg/m³)")
    ax.set_title(
        "Las barras naranjas son los empalmes de las ejecuciones del pronóstico de CAMS",
        loc="left",
        fontsize=9,
        color=INK_MUTED,
    )
    return _finish(fig, "Diagnóstico de empalmes de PM2.5", period_text(start, end))


# --- Gráficas del modelo -----------------------------------------------------------------


def _test_period(result: RegressionResult) -> str:
    return period_text(result.split.test_start, result.split.test_end) + " · periodo de prueba"


def actual_vs_predicted(result: RegressionResult) -> Figure:
    """Dispersión real frente a predicho con y = x, y las dos series en el tiempo."""
    pred = result.predictions
    fig, axes = _figure(1, 2, size=(12, 4.8))
    ax = axes[0, 0]
    ax.scatter(pred["real"], pred["predicho"], s=6, color=SERIES_1, alpha=0.3, linewidths=0)
    low = min(pred["real"].min(), pred["predicho"].min())
    high = max(pred["real"].max(), pred["predicho"].max())
    ax.plot([low, high], [low, high], color=INK_SECONDARY, linewidth=1)
    ax.annotate("y = x", (high, high), ha="right", va="bottom", color=INK_SECONDARY)
    ax.set_xlabel("PM2.5 real (µg/m³)")
    ax.set_ylabel("PM2.5 predicho (µg/m³)")

    ax = axes[0, 1]
    local = pred.tz_convert(LOCAL_TZ)
    ax.plot(local.index, local["real"], color=SERIES_1, linewidth=1, label="real")
    ax.plot(local.index, local["predicho"], color=SERIES_2, linewidth=1, label="predicho")
    ax.set_xlabel("Fecha (hora de Medellín)")
    ax.set_ylabel(label("pm25_ug_m3"))
    ax.legend(loc="upper right", frameon=False)
    ax.tick_params(axis="x", labelrotation=20)
    return _finish(fig, "Real frente a predicho", _test_period(result))


def residuals(result: RegressionResult) -> Figure:
    """Residuos frente a predichos, en el tiempo e histograma (periodo de prueba)."""
    pred = result.predictions
    fig, axes = _figure(1, 3, size=(13, 4.5))
    ax = axes[0, 0]
    ax.scatter(pred["predicho"], pred["residuo"], s=6, color=SERIES_1, alpha=0.3, linewidths=0)
    ax.axhline(0, color=INK_SECONDARY, linewidth=1)
    ax.set_xlabel("PM2.5 predicho (µg/m³)")
    ax.set_ylabel("Residuo (µg/m³)")

    ax = axes[0, 1]
    local = pred.tz_convert(LOCAL_TZ)
    ax.plot(local.index, local["residuo"], color=SERIES_1, linewidth=0.8)
    ax.axhline(0, color=INK_SECONDARY, linewidth=1)
    ax.set_xlabel("Fecha (hora de Medellín)")
    ax.set_ylabel("Residuo (µg/m³)")
    ax.tick_params(axis="x", labelrotation=20)
    ax.set_title(
        f"Durbin-Watson = {result.durbin_watson:.2f}", loc="left", fontsize=9, color=INK_MUTED
    )

    ax = axes[0, 2]
    ax.hist(pred["residuo"], bins=40, color=SERIES_1, edgecolor=SURFACE, linewidth=0.5)
    ax.set_xlabel("Residuo (µg/m³)")
    ax.set_ylabel("Número de horas")
    return _finish(fig, "Residuos del modelo", _test_period(result))


# --- Gráficas de los modelos de calendario ------------------------------------------------


def hour_effects(models: dict, start: datetime, end: datetime) -> Figure:
    """Efecto de cada hora local frente a la medianoche en los modelos de calendario."""
    fig, axes = _figure(1, len(models), size=(13, 4.5))
    for ax, (variable, model) in zip(axes.flat, models.items(), strict=True):
        effects = model.hour_effects
        ax.bar(effects.index, effects.to_numpy(), color=SERIES_1, width=0.8)
        ax.axhline(0, color=INK_SECONDARY, linewidth=1)
        ax.set_xticks(range(0, 24, 3))
        ax.set_xlabel("Hora local")
        ax.set_ylabel(f"Diferencia con la medianoche ({UNITS[variable]})")
        ax.set_title(NAMES[variable], loc="left", fontsize=10)
    return _finish(fig, "Modelos de calendario: efecto de cada hora", period_text(start, end))


def prediction_chart(table: pd.DataFrame, models: dict) -> Figure:
    """Predicción horaria con una banda de ± error típico y los valores reales si existen."""
    fig, axes = _figure(len(models), 1, size=(11, 2.8 * len(models)))
    for ax, (variable, model) in zip(axes.flat, models.items(), strict=True):
        predicted = table[(variable, "prediccion")]
        error = model.typical_error
        ax.fill_between(
            table.index,
            predicted - error,
            predicted + error,
            color=SERIES_1,
            alpha=0.15,
            linewidth=0,
            label=f"± error típico ({error:.1f})",
        )
        ax.plot(table.index, predicted, color=SERIES_1, linewidth=2, label="valor típico")
        real = table[(variable, "real")]
        if real.notna().any():
            ax.plot(table.index, real, color=SERIES_2, linewidth=1.5, label="real")
        ax.set_ylabel(label(variable))
        ax.legend(loc="upper right", frameon=False, ncol=3)
    axes.flat[-1].set_xlabel("Fecha y hora (hora de Medellín)")
    first, last = table.index[0], table.index[-1]
    period = f"Periodo: {first:%Y-%m-%d %H:%M} → {last:%Y-%m-%d %H:%M} (hora de Medellín)"
    return _finish(fig, "Predicción con los modelos de calendario", period)


# --- Salida --------------------------------------------------------------------------------

NON_INTERACTIVE = {"agg", "pdf", "svg", "ps", "cairo", "template", "pgf"}


def has_display() -> bool:
    """¿Se puede abrir una ventana? No con un backend de archivo ni en Linux sin pantalla."""
    if matplotlib.get_backend().lower() in NON_INTERACTIVE:
        return False
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


@dataclass(frozen=True)
class Output:
    path: Path | None
    notice: str | None = None


def _png_path(name: str, outputs_dir: Path) -> Path:
    stamp = datetime.now(LOCAL_TZ).strftime("%Y%m%d-%H%M%S")
    path = outputs_dir / f"{name}_{stamp}.png"
    counter = 2
    while path.exists():  # nunca se sobrescribe un resultado anterior
        path = outputs_dir / f"{name}_{stamp}-{counter}.png"
        counter += 1
    return path


def save_or_show(
    fig: Figure, name: str, mode: str, outputs_dir: Path = paths.OUTPUTS_DIR
) -> Output:
    """Muestra la figura en una ventana o la guarda como PNG (DP-10)."""
    notice = None
    if mode == "ventana":
        if has_display():
            plt.show()
            plt.close(fig)
            return Output(path=None)
        notice = "No hay pantalla disponible: la gráfica se guarda como PNG."
    outputs_dir.mkdir(parents=True, exist_ok=True)
    path = _png_path(name, outputs_dir)
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    if notice:
        notice = f"{notice} Ruta: {path}"
    return Output(path=path, notice=notice)
