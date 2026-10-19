"""Pruebas de las funciones puras de cobertura."""

from datetime import UTC, date, datetime

import pandas as pd
import pytest

from clima_medellin import coverage as cov


@pytest.mark.parametrize(
    ("today", "start", "days"),
    [
        (date(2026, 10, 9), date(2025, 10, 9), 365),
        (date(2028, 2, 29), date(2027, 2, 28), 366),
        (date(2028, 3, 1), date(2027, 3, 1), 366),
        (date(2029, 3, 1), date(2028, 3, 1), 365),
    ],
)
def test_window_days(today, start, days):
    win = cov.window(today)
    assert win.start_local == start
    assert win.end_local == today
    assert win.days == days


def test_window_bounds_are_local_midnight_in_utc():
    win = cov.window(date(2026, 10, 18))
    assert win.start_utc == datetime(2025, 10, 18, 5, tzinfo=UTC)
    assert win.end_utc == datetime(2026, 10, 18, 5, tzinfo=UTC)


def test_effective_end_per_source():
    today = date(2026, 10, 18)
    win = cov.window(today)
    assert cov.effective_end("ERA5", win, today) == datetime(2026, 10, 14, tzinfo=UTC)
    assert cov.effective_end("CAMS_GLOBAL", win, today) == datetime(2026, 10, 18, 5, tzinfo=UTC)


def test_expected_steps_are_hourly_and_half_open():
    steps = cov.expected_steps(
        datetime(2026, 3, 1, 5, tzinfo=UTC), datetime(2026, 3, 1, 8, tzinfo=UTC)
    )
    assert [ts.hour for ts in steps] == [5, 6, 7]
    assert str(steps.tz) == "UTC"


def hours(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="h", tz="UTC")


def test_documentation_example_yields_two_one_day_requests():
    missing = hours("2026-03-03 13:00", "2026-03-03 18:00").append(
        hours("2026-03-10 00:00", "2026-03-10 23:00")
    )
    intervals = cov.group_intervals(missing)
    assert len(intervals) == 2
    assert cov.to_request_dates(intervals) == [
        (date(2026, 3, 3), date(2026, 3, 3)),
        (date(2026, 3, 10), date(2026, 3, 10)),
    ]


def test_contiguous_days_merge_into_one_request():
    missing = hours("2026-03-03 22:00", "2026-03-04 02:00")
    assert cov.to_request_dates(cov.group_intervals(missing)) == [
        (date(2026, 3, 3), date(2026, 3, 4))
    ]


def test_ranges_one_day_apart_merge_but_two_days_apart_do_not():
    missing = (
        hours("2026-03-01 10:00", "2026-03-01 11:00")
        .append(hours("2026-03-02 10:00", "2026-03-02 11:00"))
        .append(hours("2026-03-05 10:00", "2026-03-05 11:00"))
    )
    assert cov.to_request_dates(cov.group_intervals(missing)) == [
        (date(2026, 3, 1), date(2026, 3, 2)),
        (date(2026, 3, 5), date(2026, 3, 5)),
    ]


YEAR = hours("2025-01-01 00:00", "2025-12-31 23:00")  # 8 760 horas


def test_six_hour_gap_is_still_complete():
    valid = YEAR.delete(range(100, 106))
    result = cov.variable_coverage("x", YEAR, valid)
    assert result.expected == 8760
    assert result.valid == 8754
    assert round(result.percent, 2) == 99.93
    assert result.max_gap_hours == 6
    assert result.gaps == 1
    assert cov.state_of(8754, [result]) == "COMPLETA"


def test_seven_hour_gap_is_partial():
    result = cov.variable_coverage("x", YEAR, YEAR.delete(range(100, 107)))
    assert result.max_gap_hours == 7
    assert cov.state_of(8753, [result]) == "PARCIAL"


def test_low_percentage_with_short_gaps_is_partial():
    valid = YEAR.delete(range(0, len(YEAR), 34))  # ~3 % en huecos de 1 hora
    result = cov.variable_coverage("x", YEAR, valid)
    assert 96.5 < result.percent < 97.5
    assert result.max_gap_hours == 1
    assert cov.state_of(len(valid), [result]) == "PARCIAL"


def test_no_records_is_sin_datos():
    result = cov.variable_coverage("x", YEAR, pd.DatetimeIndex([], tz="UTC"))
    assert result.percent == 0
    assert cov.state_of(0, [result]) == "SIN_DATOS"


def test_report_counts_only_the_window_and_each_variable():
    today = date(2026, 10, 18)
    win = cov.window(today)
    index = cov.expected_steps(win.start_utc, win.end_utc)
    existing = pd.DataFrame({"pm25_ug_m3": True}, index=index)
    existing.loc[index[10:13], "pm25_ug_m3"] = False  # 3 horas con el valor nulo
    before = pd.DataFrame(
        {"pm25_ug_m3": [True]}, index=pd.DatetimeIndex([win.start_utc], tz="UTC") - cov.STEP
    )
    report = cov.coverage_report("CAMS_GLOBAL", pd.concat([before, existing]), win, today)
    assert report.records_in_window == 8760
    (pm,) = report.variables
    assert pm.valid == 8757 and pm.max_gap_hours == 3
    assert report.state == "COMPLETA"
    assert len(report.missing) == 0
