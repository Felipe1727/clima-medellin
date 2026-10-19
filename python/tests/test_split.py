"""Pruebas de la separación temporal (D-018)."""

from datetime import UTC, date, datetime

import pandas as pd

from clima_medellin.coverage import window
from clima_medellin.split import add_months, temporal_split


def test_october_window_split():
    split = temporal_split(window(date(2026, 10, 18)))
    assert split.train_start == datetime(2025, 10, 18, 5, tzinfo=UTC)
    assert split.train_end == datetime(2026, 7, 18, 5, tzinfo=UTC)
    assert split.test_start == datetime(2026, 7, 19, 5, tzinfo=UTC)
    assert split.test_end == datetime(2026, 10, 18, 5, tzinfo=UTC)


def test_missing_day_nine_months_later_uses_the_last_day_of_the_month():
    assert add_months(date(2027, 5, 31), 9) == date(2028, 2, 29)
    assert add_months(date(2026, 5, 31), 9) == date(2027, 2, 28)
    split = temporal_split(window(date(2028, 5, 31)))
    assert split.train_end == datetime(2028, 2, 29, 5, tzinfo=UTC)


def test_train_and_test_filters_are_half_open_and_skip_the_gap():
    split = temporal_split(window(date(2026, 10, 18)))
    index = pd.date_range(split.train_end - pd.Timedelta(hours=1), periods=27, freq="h", tz="UTC")
    frame = pd.DataFrame({"x": range(len(index))}, index=index)
    assert list(split.train(frame).index) == [index[0]]
    test = split.test(frame)
    assert test.index[0] == pd.Timestamp(split.test_start)
    assert len(test) == 2
