from datetime import date

from heatcore.climatology import normal_for


def test_window_mean_ignores_outside_years_and_days():
    data = {"1995-04-16": 35.0, "2000-04-10": 37.0, "2021-04-16": 50.0, "1995-05-30": 50.0}
    assert normal_for(date(2023, 4, 16), data) == 36.0
