from datetime import datetime

import pytest

from heatcore.sitebox import LIMIT_C, evaluate, measured_wbgt, stull_wet_bulb

NOON = datetime(2026, 5, 15, 12, 50)


def test_stull_reference_value():
    # Stull 2011 worked example: 20 C, 50% RH -> 13.7 C
    assert stull_wet_bulb(20, 50) == pytest.approx(13.7, abs=0.1)


def test_globe_raises_wbgt():
    assert measured_wbgt(36, 60, 50) > measured_wbgt(36, 60, 36) + 2


def test_hot_reading_turns_on_fan_siren_and_light():
    s = evaluate({"temp_c": 38, "rh": 65, "globe_c": 47, "light_raw": 4000, "tank_distance_cm": 100,
                  "drain_distance_cm": 80}, now=NOON)
    assert s["limit_c"] == LIMIT_C == 28.2 and s["level_index"] == 4 and s["stop_now"] and s["aaram_now"]
    assert s["fan_on"] and s["pump_on"] and s["readings"]["tank_pct"] == 17 and "tank_low" in s["alerts"]
    assert all(len(line) <= 21 for line in s["display"]) and s["color"] == "#A266B0"


def test_cool_reading_and_pump_hysteresis():
    s = evaluate({"temp_c": 24, "rh": 40, "globe_c": 26, "tank_distance_cm": 60}, now=NOON, prev_pump=True)
    assert s["level"] == "kam" and not s["fan_on"] and s["pump_on"]  # 50% full, keep refilling
    s2 = evaluate({"temp_c": 24, "rh": 40, "globe_c": 26, "tank_distance_cm": 6}, now=NOON, prev_pump=True)
    assert not s2["pump_on"]  # 95% full -> stop


def test_rest_window_is_end_of_hour():
    r = {"temp_c": 33, "rh": 55, "globe_c": 36}
    s_early = evaluate(r, now=datetime(2026, 5, 15, 12, 5))
    s_late = evaluate(r, now=datetime(2026, 5, 15, 12, 58))
    assert 0 < s_early["rest_minutes"] < 60 and not s_early["aaram_now"] and s_late["aaram_now"]


def test_drain_and_sos_alerts():
    s = evaluate({"temp_c": 30, "rh": 80, "drain_distance_cm": 55, "sos": True}, fallback_wbgt_c=29.0, now=NOON)
    assert "waterlogging" in s["alerts"] and "sos" in s["alerts"] and s["wbgt_source"] == "forecast_radiation"


def test_rejects_bad_air():
    with pytest.raises(ValueError):
        evaluate({"temp_c": 99, "rh": 50})
