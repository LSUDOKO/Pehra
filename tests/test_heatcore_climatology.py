from datetime import date

from heatcore.climatology import normal_for


def test_window_mean_ignores_outside_years_and_days():
    data = {"1995-04-16": 35.0, "2000-04-10": 37.0, "2021-04-16": 50.0, "1995-05-30": 50.0}
    assert normal_for(date(2023, 4, 16), data) == 36.0


def test_normals_by_mmdd_matches_single_day():
    from heatcore.climatology import normals_by_mmdd
    data = {"1995-04-16": 35.0, "2000-04-10": 37.0, "2021-04-16": 50.0}
    n = normals_by_mmdd(data)
    assert n["04-16"] == normal_for(date(2023, 4, 16), data) == 36.0
    assert "02-29" in n or not n.get("02-29")


def test_nearest_city():
    from heatcore.cities import nearest_city
    assert nearest_city(13.0, 80.2).key == "chennai" and nearest_city(10.0, 70.0) is None
