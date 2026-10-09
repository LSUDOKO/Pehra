from heatcore.imd_rule import Level, day_level, district_flags


def test_exactly_40_plains_needs_departure():
    assert day_level(40.0, 35.5, "plains") == Level.HEATWAVE   # departure 4.5
    assert day_level(40.0, 36.0, "plains") == Level.NONE       # departure 4.0
    assert day_level(39.9, 30.0, "plains") == Level.NONE       # below threshold


def test_absolute_45_and_47():
    assert day_level(45.0, 44.0) == Level.HEATWAVE
    assert day_level(47.0, 46.0) == Level.SEVERE


def test_severe_by_departure():
    assert day_level(41.0, 34.5) == Level.SEVERE  # departure 6.5


def test_coastal_threshold():
    assert day_level(37.0, 32.5, "coastal") == Level.HEATWAVE


def test_two_day_persistence():
    hot, normal = [41, 41, 30, 41, 30], [35] * 5
    flags = district_flags([hot, hot], [normal, normal])
    assert flags == [True, True, False, False, False]


def test_needs_two_cells():
    hot, cool, normal = [41, 41], [30, 30], [35, 35]
    assert district_flags([hot, cool], [normal, normal]) == [False, False]
    assert district_flags([hot], [normal]) == [True, True]  # single-cell district
