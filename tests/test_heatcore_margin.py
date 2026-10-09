from datetime import datetime, timedelta

from heatcore.margin import planning_margin

NOW = datetime(2026, 10, 10, 19, 0)


def test_fresh_forecast_margin():
    assert planning_margin(NOW - timedelta(hours=6), NOW) == (1.0, False)


def test_stale_forecast_adds_half_degree():
    assert planning_margin(NOW - timedelta(hours=19), NOW) == (1.5, True)


def test_exactly_18h_is_not_stale():
    assert planning_margin(NOW - timedelta(hours=18), NOW) == (1.0, False)
