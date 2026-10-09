import json
from pathlib import Path

from heatcore.heat import compute_heat, for_date, heat_from_json, heat_to_json
from heatcore.openmeteo import parse_hourly

FIX = Path(__file__).parent / "fixtures" / "openmeteo_kharghar_2023-04-16.json"


def load():
    return parse_hourly(json.loads(FIX.read_text()))


def test_parse_recorded_payload():
    rows = load()
    assert len(rows) == 24 and rows[0].time_utc.tzinfo is not None
    assert all(0 <= r.rh_pct <= 100 for r in rows)


def test_heat_is_in_ist_and_roundtrips():
    heat = compute_heat(load(), 19.04, 73.07)
    assert heat[0].time_local.hour == 5 and heat[0].time_local.minute == 0
    assert heat_from_json(heat_to_json(heat)) == heat


def test_for_date_filters_local_day():
    heat = compute_heat(load(), 19.04, 73.07)
    assert all(h.time_local.day == 16 for h in for_date(heat, "2023-04-16"))
