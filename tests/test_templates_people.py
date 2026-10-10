import re
from datetime import datetime, timedelta

from heatcore.personal import Household, personal_forecast
from heatcore.plan import HourHeat
from heatcore.templates_people import family_call_text, personal_message, places_reply, site_rain_line

D = datetime(2026, 5, 15)
HEAT = [HourHeat(D + timedelta(hours=h), v, v - 3)
        for h, v in enumerate([26] * 7 + [27, 28, 29, 30, 31, 32, 32, 31, 30, 29, 28] + [26] * 6)]


def test_personal_message_numbers_from_code_and_no_safe():
    f = personal_forecast(HEAT, Household(adults=2, elderly=1, works_outdoors=True))
    cond = {"rain": {"alert": True, "category": "heavy", "total_mm": 80.2},
            "night": {"warm_night": "warm", "night_min_c": 31.4}, "flood": None}
    msg = personal_message("Chennai", f, cond, "Forecast: X, 10 Oct 12:00 IST.")
    assert "80.2 mm" in msg and "31.4" in msg and "Buzurg" in msg and "safe" not in msg.lower()
    hours = {str(h) for h in range(1, 13)}
    for n in re.findall(r"(\d+) se (\d+) baje", msg):
        assert set(n) <= hours


def test_family_call_and_places_and_site_rain():
    f = personal_forecast(HEAT, Household(elderly=1))
    assert "108" in family_call_text("Delhi", f)
    assert "OpenStreetMap" in places_reply([{"kind": "drinking_water", "name": "Pyau", "distance_m": 120,
                                             "link": "https://maps.google.com/?q=1,2"}], 5)
    assert "5 km" in places_reply([], 0)
    assert site_rain_line({"alert": False}) is None and "khudai" in site_rain_line(
        {"alert": True, "category": "very_heavy", "total_mm": 130})
