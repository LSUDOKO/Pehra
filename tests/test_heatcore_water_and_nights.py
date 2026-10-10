from datetime import UTC, datetime

import pytest

from heatcore.flood import flood_signal, percentile
from heatcore.nights import night_summary, warm_night
from heatcore.places import distance_km, map_link, nearest
from heatcore.rain import category, daily_rain
from heatcore.sensor import compare, drain_level_cm, site_wbgt, tank_percent


@pytest.mark.parametrize("mm, cat", [(0, "none"), (2.4, "very_light"), (15.5, "light"), (64.4, "moderate"),
                                     (64.5, "heavy"), (115.6, "very_heavy"), (204.5, "extremely_heavy")])
def test_imd_rain_categories(mm, cat):
    assert category(mm) == cat


def test_daily_rain_sums_local_day():
    rows = [{"t": f"2026-07-01T{h:02d}:00", "precip": 10, "pprob": 80} for h in range(7)]
    rows.append({"t": "2026-07-02T01:00", "precip": 50})
    r = daily_rain(rows, "2026-07-01")
    assert r["total_mm"] == 70 and r["alert"] and r["wet_hours"] == list(range(7))


@pytest.mark.parametrize("tmax, tmin, normal, out", [(39.9, 35, 25, "none"), (41, 29.5, 25, "warm"),
                                                     (41, 31.5, 25, "very_warm"), (42, 28, 25, "none")])
def test_imd_warm_night(tmax, tmin, normal, out):
    assert warm_night(tmax, tmin, normal) == out


def test_night_summary_spans_midnight():
    rows = [{"t": "2026-05-01T21:00", "temp": 33}, {"t": "2026-05-02T04:00", "temp": 30},
            {"t": "2026-05-01T14:00", "temp": 42}]
    assert night_summary(rows, "2026-05-01") == {"night_min_c": 30, "day_max_c": 42}


def test_nearest_points_sorted_and_filtered():
    pts = [{"lat": 28.6315, "lon": 77.2167, "kind": "drinking_water", "name": "A"},
           {"lat": 28.6400, "lon": 77.2167, "kind": "shelter", "name": "B"},
           {"lat": 29.5, "lon": 77.2, "kind": "drinking_water", "name": "far"}]
    got = nearest(pts, 28.6310, 77.2160)
    assert [p["name"] for p in got] == ["A", "B"] and got[0]["distance_m"] < 200
    assert abs(distance_km(0, 0, 0, 1) - 111.2) < 0.2 and "maps.google.com" in map_link(1, 2)


def test_flood_signal_levels():
    hist = list(range(1, 101))
    assert percentile(hist, 0.95) == 95.0
    assert flood_signal([50, 99.5], hist)["level"] == "severe"
    assert flood_signal([96], hist)["level"] == "high"
    assert flood_signal([None], hist) == {"available": False}


def test_sensor_site_wbgt_and_compare():
    wx = {"pressure": 1005, "wind": 2, "ghi": 800, "direct": 500}
    hot = site_wbgt(datetime(2026, 5, 15, 7, 0, tzinfo=UTC), 13.08, 80.27, 38, 60, wx)
    cool = site_wbgt(datetime(2026, 5, 15, 7, 0, tzinfo=UTC), 13.08, 80.27, 33, 60, wx)
    assert hot["wbgt_sun"] > cool["wbgt_sun"]
    assert compare(33.5, 32.0)["hotter"] and not compare(32.5, 32.0)["hotter"]
    with pytest.raises(ValueError):
        site_wbgt(datetime(2026, 5, 15, tzinfo=UTC), 0, 0, 90, 50, wx)


def test_tank_and_drain_levels():
    assert tank_percent(20, 100) == 80 and tank_percent(150, 100) == 0
    assert drain_level_cm(70, 100) == 30 and drain_level_cm(120, 100) == 0
