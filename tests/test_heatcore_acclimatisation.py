import pytest

from heatcore.acclimatisation import (
    new_worker_fraction,
    reduced_work_minutes,
    returning_worker_fraction,
    uses_ral,
)


@pytest.mark.parametrize("day, f", [(1, 0.2), (2, 0.4), (3, 0.6), (4, 0.8), (5, 1.0), (9, 1.0)])
def test_new_worker_days(day, f):
    assert new_worker_fraction(day) == f


@pytest.mark.parametrize("day, f", [(1, 0.5), (2, 0.6), (3, 0.8), (4, 1.0), (7, 1.0)])
def test_returning_worker_days(day, f):
    assert returning_worker_fraction(day) == f


def test_ral_until_day_5():
    assert uses_ral(4) and not uses_ral(5)


def test_reduced_minutes_never_increase():
    assert reduced_work_minutes([60, 45, 0], 0.2) == [12, 9, 0]
    assert reduced_work_minutes([60], 1.7) == [60]


def test_day_zero_rejected():
    with pytest.raises(ValueError):
        new_worker_fraction(0)
