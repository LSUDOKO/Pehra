"""Weather rows -> hourly heat in local (IST) time, and the cached JSON form.

Open-Meteo radiation is the mean over the hour *before* each UTC label, so each
row is centred 30 min earlier. In IST (UTC+5:30) that lands on a whole hour.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from heatcore.plan import HourHeat
from heatcore.wbgt import HourWeather, wbgt_hour

IST = timezone(timedelta(hours=5, minutes=30))


def compute_heat(rows: list[HourWeather], lat: float, lon: float) -> list[HourHeat]:
    out = []
    for r in rows:
        mid = replace(r, time_utc=r.time_utc - timedelta(minutes=30))
        w = wbgt_hour(mid, lat, lon)
        local = mid.time_utc.astimezone(IST).replace(tzinfo=None)
        out.append(HourHeat(local, w["wbgt_sun"], w["wbgt_shade"]))
    return out


def heat_to_json(heat: list[HourHeat]) -> list[dict]:
    return [{"t": h.time_local.isoformat(), "sun": h.wbgt_sun, "shade": h.wbgt_shade}
            for h in heat]


def heat_from_json(rows: list[dict]) -> list[HourHeat]:
    return [HourHeat(datetime.fromisoformat(r["t"]), r["sun"], r["shade"]) for r in rows]


def for_date(heat: list[HourHeat], day: str) -> list[HourHeat]:
    return [h for h in heat if h.time_local.date().isoformat() == day]
