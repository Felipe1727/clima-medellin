"""Actualización incremental con el JAR real, una base temporal y la API falsa."""

from datetime import UTC, date, datetime

import pandas as pd
import pytest
from fakes import FakeOpenMeteo

from clima_medellin import paths
from clima_medellin.bridge import JavaBridge
from clima_medellin.update import PlannedRequest, current_coverage, plan_update, update

TODAY = date(2026, 10, 18)
ERA5_END = datetime(2026, 10, 14, tzinfo=UTC)


@pytest.fixture
def bridge(tmp_path) -> JavaBridge:
    assert paths.JAR_PATH.is_file(), f"Falta {paths.JAR_PATH}"
    return JavaBridge(
        tmp_path / "data" / "test.odb",
        staging_dir=tmp_path / "staging",
        exchange_dir=tmp_path / "exchange",
    )


def test_initial_load_is_complete_and_second_update_plans_nothing(bridge):
    fake = FakeOpenMeteo(TODAY)

    outcome = update(bridge, TODAY, fetch=fake)

    assert {(c[0], c[1], c[2]) for c in fake.calls} == {
        ("ERA5", date(2025, 10, 18), date(2026, 10, 13)),
        ("CAMS_GLOBAL", date(2025, 10, 18), date(2026, 10, 18)),
    }
    assert outcome.coverage["ERA5"].state == "COMPLETA"
    assert outcome.coverage["CAMS_GLOBAL"].state == "COMPLETA"
    era5 = outcome.coverage["ERA5"]
    assert era5.records_in_window == 8659
    assert all(v.valid == 8659 for v in era5.variables)
    assert outcome.coverage["CAMS_GLOBAL"].records_in_window == 8760
    assert all(r.outside_window == 5 for r in outcome.results)

    stored = bridge.coverage("ERA5").summary
    assert pd.Timestamp(stored["last"]) < pd.Timestamp(ERA5_END)
    assert stored["count"] == 8659

    assert plan_update(bridge, TODAY).requests == []


def test_a_missing_day_is_the_only_request(bridge):
    hole = date(2026, 3, 10)
    first = update(bridge, TODAY, fetch=FakeOpenMeteo(TODAY, skip={"ERA5": {hole}}))
    era5 = first.coverage["ERA5"]
    assert era5.state == "PARCIAL"
    assert all(v.max_gap_hours == 24 for v in era5.variables)

    plan = plan_update(bridge, TODAY)

    assert plan.requests == [PlannedRequest("ERA5", hole, hole)]
    second = update(bridge, TODAY, fetch=FakeOpenMeteo(TODAY))
    assert second.coverage["ERA5"].state == "COMPLETA"


def test_empty_api_answer_still_records_a_batch(bridge):
    outcome = update(bridge, TODAY, fetch=FakeOpenMeteo(TODAY, empty=True))

    assert len(outcome.results) == 2
    for result in outcome.results:
        assert result.imported["batch_id"]
        assert result.imported["received"] == 0
        assert result.imported["inserted"] == 0
    assert {r.state for r in current_coverage(bridge, TODAY).values()} == {"SIN_DATOS"}
