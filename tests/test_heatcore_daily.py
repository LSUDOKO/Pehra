from datetime import datetime, timedelta

import pytest

from heatcore.daily import Crew, ForecastMeta, build_daily_plan
from heatcore.plan import HourHeat

D = datetime(2026, 10, 11)
VALS = [25] * 8 + [27, 28, 29, 31, 32, 32, 31, 29, 28, 27] + [25] * 6
HEAT = [HourHeat(D + timedelta(hours=i), v, v - 3) for i, v in enumerate(VALS)]
FC = ForecastMeta("open-meteo", datetime(2026, 10, 10, 12))
NOW = datetime(2026, 10, 10, 19)


DEFAULT_CREW = Crew(40, 10, 3, 1)


def plan(crew=DEFAULT_CREW, now=NOW):
    return build_daily_plan(HEAT, crew, FC, now, site_id="s1", site_name="Test")


def test_shape_and_stop_window():
    p = plan()
    assert p["stop_from"] == 11 and p["stop_to"] == 15
    assert set(p["plans"]) == {"moderate", "heavy"}
    assert p["water"]["cans_20l"] > 0 and p["new_workers"]["fraction"] == 0.2


def test_no_new_line_without_new_workers():
    assert plan(Crew(20, 0, 0))["new_workers"] is None


def test_stale_forecast_widens_margin():
    p = plan(now=NOW + timedelta(hours=12))
    assert p["stale"] and p["margin_c"] == 1.5


def test_hash_is_deterministic_and_ignores_generated_at():
    a, b = plan(), plan()
    assert a["plan_hash"] == b["plan_hash"]


def test_crew_validation():
    with pytest.raises(ValueError):
        Crew(5, 4, 3)
