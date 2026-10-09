import copy
from datetime import datetime, timedelta

import pytest

from heatcore.guard import LooserPlanError, assert_not_looser, direction
from heatcore.plan import HourHeat, build_plan

DAY = datetime(2026, 5, 15)
BASE = build_plan([HourHeat(DAY + timedelta(hours=h), 29.5, 27) for h in range(24)], margin_c=1.0)


def test_never_looser_rejects_less_rest():
    ai = copy.deepcopy(BASE)
    ai.hours[5].rest_minutes -= 15
    with pytest.raises(LooserPlanError):
        assert_not_looser(BASE, ai)
    assert direction(BASE, ai) == "looser"


def test_stricter_plan_allowed():
    ai = copy.deepcopy(BASE)
    ai.hours[5].rest_minutes = 60
    assert_not_looser(BASE, ai)
    assert direction(BASE, ai) == "stricter"


def test_dropping_an_hour_counts_as_looser():
    ai = copy.deepcopy(BASE)
    ai.hours.pop(3)
    assert direction(BASE, ai) == "looser"


def test_same_plan():
    assert direction(BASE, copy.deepcopy(BASE)) == "same"
