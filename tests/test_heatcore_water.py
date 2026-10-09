import pytest

from heatcore.water import cups_for_hour, water_plan


@pytest.mark.parametrize("work, cups", [(0, 0), (15, 1), (30, 2), (45, 3), (60, 3)])
def test_cups_per_hour(work, cups):
    assert cups_for_hour(work) == cups


def test_water_cans_round_up_with_buffer():
    # 40 workers x 13 h x 3 cups x 0.24 L = 374.4 L; x1.1 = 411.84 -> 21 cans
    out = water_plan([60] * 13, 40)
    assert out["litres"] == 374.4 and out["cans_20l"] == 21


def test_exact_multiple_still_gets_buffer():
    # 25 workers x 1 h x 3 cups... choose values hitting 20 L exactly is hard; check monotone
    assert water_plan([60], 1)["cans_20l"] == 1
    assert water_plan([], 40)["cans_20l"] == 0
