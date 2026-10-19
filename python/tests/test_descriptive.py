"""Estadísticas descriptivas."""

import numpy as np
import pandas as pd
import pytest

from clima_medellin.descriptive import describe_bands, describe_variables


def test_known_series():
    values = list(range(1, 101)) + [np.nan] * 3
    index = pd.date_range("2026-01-01", periods=len(values), freq="h", tz="UTC")
    stats = describe_variables(pd.DataFrame({"x": values}, index=index)).loc["x"]
    assert stats["n"] == 100 and stats["nulos"] == 3
    assert stats["media"] == 50.5 and stats["mediana"] == 50.5
    assert stats["min"] == 1 and stats["max"] == 100
    assert stats["p25"] == pytest.approx(25.75)
    assert stats["p5"] == pytest.approx(5.95)
    assert stats["p95"] == pytest.approx(95.05)
    assert stats["desv"] == pytest.approx(np.std(range(1, 101), ddof=1))


def test_valid_days_per_band():
    columns = pd.MultiIndex.from_product([["x"], ["mañana", "tarde"]])
    bands = pd.DataFrame([[1.0, 4.0], [np.nan, 5.0], [3.0, 6.0]], columns=columns)
    stats = describe_bands(bands)
    assert stats.loc[("x", "mañana"), "dias_validos"] == 2
    assert stats.loc[("x", "mañana"), "media"] == 2.0
    assert stats.loc[("x", "tarde"), "dias_validos"] == 3
