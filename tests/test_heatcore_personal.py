from datetime import datetime, timedelta

import pytest

from heatcore.personal import Household, group_limits, level_for, personal_forecast
from heatcore.plan import HourHeat

D = datetime(2026, 5, 15)
PROFILE = [26] * 7 + [27, 28, 29, 30, 31, 32, 32, 31, 30, 29, 28] + [26] * 6


def heat(vals=PROFILE):
    return [HourHeat(D + timedelta(hours=h), v, v - 3) for h, v in enumerate(vals)]


@pytest.mark.parametrize("e, lvl", [(-1, 0), (0, 0), (0.5, 1), (1, 1), (1.5, 2), (2.5, 3), (3.01, 4)])
def test_levels_share_work_band_edges(e, lvl):
    assert level_for(e) == lvl


def test_vulnerable_uses_stricter_limit():
    lim = group_limits(Household(adults=2, elderly=1, works_outdoors=True))
    assert lim == {"adults": 30.8, "vulnerable": 28.1, "outdoor_worker": 28.2}


def test_vulnerable_peak_is_worse_and_windows_are_morning():
    f = personal_forecast(heat(), Household(adults=2, elderly=1), margin_c=1.0)
    g = f["groups"]
    order = ["kam", "saavdhaan", "zyada", "bahut_zyada", "khatarnak"]
    assert order.index(g["vulnerable"]["peak_level"]) > order.index(g["adults"]["peak_level"])
    assert f["better_windows"][0][0] == 6 and g["vulnerable"]["avoid"]


def test_healthy_adult_only_household():
    f = personal_forecast(heat([20] * 24), Household())
    assert set(f["groups"]) == {"adults"} and f["overall_level"] == "kam"


def test_negative_counts_rejected():
    with pytest.raises(ValueError):
        Household(elderly=-1)
