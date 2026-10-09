from datetime import datetime, timedelta

from heatcore.plan import HourHeat
from heatcore.reschedule import find_window

DAY = datetime(2026, 5, 15)


def days(*per_day):
    out = []
    for d, vals in enumerate(per_day):
        for hr, v in enumerate(vals):
            out.append(HourHeat(DAY + timedelta(days=d, hours=hr), v, v - 3))
    return out


def test_picks_coolest_morning_window():
    day = [24] * 6 + [25, 25, 26, 27] + [33] * 6 + [28] * 8
    out = find_window(days(day), 4, "heavy", margin_c=0)
    assert (out["start_hour"], out["end_hour"]) == (6, 10)


def test_picks_cooler_day():
    hot, cool = [32] * 24, [22] * 24
    out = find_window(days(hot, cool), 3, "heavy", margin_c=0)
    assert out["date"] == "2026-05-16" and out["flagged"] is False


def test_flags_when_no_good_window():
    out = find_window(days([34] * 24), 4, "heavy", margin_c=1.0)
    assert out["flagged"] is True and out["status"] == "stop"
