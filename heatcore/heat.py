"""Weather rows -> hourly heat in local (IST) time, and the cached JSON form."""

from datetime import datetime, timedelta, timezone

from heatcore.plan import HourHeat
from heatcore.wbgt import HourWeather, wbgt_hour

IST = timezone(timedelta(hours=5, minutes=30))


def compute_heat(rows: list[HourWeather], lat: float, lon: float) -> list[HourHeat]:
    out = []
    for r in rows:
        w = wbgt_hour(r, lat, lon)
        local = r.time_utc.astimezone(IST).replace(tzinfo=None)
        out.append(HourHeat(local, w["wbgt_sun"], w["wbgt_shade"]))
    return out


def heat_to_json(heat: list[HourHeat]) -> list[dict]:
    return [{"t": h.time_local.isoformat(), "sun": h.wbgt_sun, "shade": h.wbgt_shade}
            for h in heat]


def heat_from_json(rows: list[dict]) -> list[HourHeat]:
    return [HourHeat(datetime.fromisoformat(r["t"]), r["sun"], r["shade"]) for r in rows]


def for_date(heat: list[HourHeat], day: str) -> list[HourHeat]:
    return [h for h in heat if h.time_local.date().isoformat() == day]
