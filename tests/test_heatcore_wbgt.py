from datetime import UTC, datetime

import pytest

from heatcore.solar import cos_zenith, erbs_direct_fraction
from heatcore.wbgt import HourWeather, wbgt_hour

CHENNAI = (13.08, 80.27)
NOON_IST = datetime(2026, 5, 15, 6, 30, tzinfo=UTC)
NIGHT_IST = datetime(2026, 5, 15, 18, 30, tzinfo=UTC)


def test_sun_hotter_than_shade_at_noon():
    out = wbgt_hour(HourWeather(NOON_IST, 35, 60, 1005, 3, 900), *CHENNAI)
    assert out["wbgt_sun"] > out["wbgt_shade"]


def test_sun_equals_shade_at_night():
    out = wbgt_hour(HourWeather(NIGHT_IST, 30, 75, 1005, 2, 0), *CHENNAI)
    assert out["wbgt_sun"] == out["wbgt_shade"]


def test_humidity_raises_wbgt():
    dry = wbgt_hour(HourWeather(NOON_IST, 36, 30, 1005, 3, 900), *CHENNAI)
    humid = wbgt_hour(HourWeather(NOON_IST, 36, 70, 1005, 3, 900), *CHENNAI)
    assert humid["wbgt_sun"] > dry["wbgt_sun"] + 2


def test_regression_values():
    # Locks current thermofeel 2.3.0 output; OSHA comparison is in docs/MODEL_CARD.md
    out = wbgt_hour(HourWeather(NOON_IST, 35, 60, 1005, 3, 900), *CHENNAI)
    assert out["wbgt_sun"] == pytest.approx(34.2, abs=0.2)
    assert out["wbgt_shade"] == pytest.approx(30.1, abs=0.2)


def test_cos_zenith_noon_high_and_night_zero():
    assert cos_zenith(*CHENNAI, NOON_IST) > 0.95
    assert cos_zenith(*CHENNAI, NIGHT_IST) == 0


def test_erbs_fraction_bounds():
    f = erbs_direct_fraction(900, 0.97, NOON_IST)
    assert 0.5 < f <= 0.9
    assert erbs_direct_fraction(0, 0.97, NOON_IST) == 0


def test_vectorised_matches_scalar():
    import numpy as np

    from heatcore.solar import cos_zenith_array
    from heatcore.wbgt import wbgt_arrays

    h = HourWeather(NOON_IST, 35, 60, 1005, 3, 900, 600)
    scalar = wbgt_hour(h, *CHENNAI)
    t = np.array([np.datetime64(NOON_IST.replace(tzinfo=None))])
    sun, shade = wbgt_arrays(*CHENNAI, t, [35], [60], [1005], [3], [900], [600])
    assert abs(cos_zenith_array(*CHENNAI, t)[0] - cos_zenith(*CHENNAI, NOON_IST)) < 1e-6
    assert sun[0] == pytest.approx(scalar["wbgt_sun"], abs=0.1)
    assert shade[0] == pytest.approx(scalar["wbgt_shade"], abs=0.1)


def test_wbgt_known_case_vs_osha_calculator():
    """15 Chennai hours vs OSHA's online calculator (fixture recorded 2026-10-09).

    OSHA prints whole degrees F (about 0.28 C resolution); tolerance 0.6 C per hour, 0.3 C mean.
    """
    import json
    from pathlib import Path

    data = json.loads((Path(__file__).parent / "fixtures/osha_wbgt_cases.json").read_text())
    diffs = []
    for c in data["cases"]:
        h = HourWeather(datetime(2026, 5, 15, c["utc_h"], 0, tzinfo=UTC), c["temp_c"], c["rh"],
                        c["p"], c["wind"], c["si"])
        diffs.append(wbgt_hour(h, 13.08, 80.27)["wbgt_sun"] - c["osha_wbgt_c"])
    assert max(abs(d) for d in diffs) <= 0.6
    assert sum(abs(d) for d in diffs) / len(diffs) <= 0.3
