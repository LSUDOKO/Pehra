from datetime import datetime, timedelta

import pytest

from heatcore.plan import HourHeat, PlanHour, build_plan, stop_window

DAY = datetime(2026, 5, 15)


def series(values, start_hour=0):
    return [HourHeat(DAY + timedelta(hours=start_hour + i), v, v - 3) for i, v in enumerate(values)]


def ph(hour, status):
    return PlanHour(hour, 0, 0, 0, 0, 60 if status == "stop" else 0, 0, status)


def test_stop_window_longest_run():
    hours = [ph(10, "stop"), ph(11, "high"), ph(12, "stop"), ph(13, "stop"), ph(14, "stop")]
    assert stop_window(hours) == (12, 15)


def test_stop_window_none():
    assert stop_window([ph(10, "high"), ph(11, "caution")]) is None


def test_plan_only_covers_workday():
    plan = build_plan(series([25] * 24), margin_c=0)
    assert [h.hour for h in plan.hours] == list(range(6, 19))


def test_plan_moderate_noon_stop():
    # moderate REL 28.2; 32.0 + 1.0 margin -> E 4.8 -> stop
    vals = [26] * 11 + [32, 32, 32] + [26] * 10
    plan = build_plan(series(vals), "moderate", margin_c=1.0)
    assert (plan.stop_from, plan.stop_to) == (11, 14)
    noon = next(h for h in plan.hours if h.hour == 12)
    assert noon.rest_minutes == 60 and noon.work_minutes == 0


def test_unacclimatised_uses_ral():
    plan = build_plan(series([26] * 24), "moderate", acclimatised=False, margin_c=0)
    assert plan.limit_c == 25.0 and plan.hours[0].status == "caution"


def test_negative_margin_rejected():
    with pytest.raises(ValueError):
        build_plan(series([26] * 24), margin_c=-0.5)
