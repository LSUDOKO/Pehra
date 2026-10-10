from heatcore.audit import LIMIT_C, audit_city, daily_max_work_wbgt, summarise

CLIM = {f"{y}-07-{d:02d}": 33.0 for y in range(1991, 2021) for d in range(1, 31)}


def test_daily_max_only_counts_work_hours():
    rows = [("2024-07-10", 3, 40.0, 40.0), ("2024-07-10", 12, 30.0, 29.0)]
    assert daily_max_work_wbgt(rows) == {"2024-07-10": (30.0, 29.0)}


def test_invisible_day_counted_outside_hot_season():
    wbgt = {"2024-07-10": (31.0, 29.5), "2024-07-11": (27.0, 26.0)}
    tmax = {"2024-07-10": 35.0, "2024-07-11": 34.0}
    rows = audit_city(wbgt, tmax, CLIM, "coastal")
    s = summarise(rows)
    assert LIMIT_C == 28.2
    assert s["invisible_days_shade"] == 1 and s["invisible_shade_outside_mar_jun"] == 1
    assert s["heatwave_days"] == 0


def test_warm_nights_and_heavy_rain_counted():
    wbgt = {"2024-05-10": (31.0, 29.5), "2024-07-11": (27.0, 26.0)}
    tmax = {"2024-05-10": 42.0, "2024-07-11": 30.0}
    clim = {f"{y}-{m}-{d:02d}": 33.0 for y in range(1991, 2021) for m in ("05", "07") for d in range(1, 31)}
    tmin_clim = {k: 25.0 for k in clim}
    rows = audit_city(wbgt, tmax, clim, "plains", {"2024-05-10": 31.0, "2024-07-11": 24.0}, tmin_clim,
                      {"2024-05-10": 0.0, "2024-07-11": 90.0})
    s = summarise(rows)
    assert s["warm_nights"] == 1 and s["heavy_rain_days"] == 1
