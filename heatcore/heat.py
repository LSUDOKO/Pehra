"""Weather rows -> hourly heat in local (IST) time, and the cached JSON form.

Open-Meteo radiation is the mean over the hour *before* each UTC label, so each
row is centred 30 min earlier. In IST (UTC+5:30) that lands on a whole hour.
"""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

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


def wx_rows(payload: dict) -> list[dict]:
    """Hourly weather in local time (same 30-minute centring as heat) for rain, nights and sensors."""
    h = payload["hourly"]
    out = []
    for i, t in enumerate(h["time"]):
        mid = datetime.fromisoformat(t).replace(tzinfo=UTC) - timedelta(minutes=30)
        local = mid.astimezone(IST).replace(tzinfo=None)

        def g(key, i=i):
            return (h.get(key) or [None] * len(h["time"]))[i]
        out.append({"t": local.isoformat(), "temp": g("temperature_2m"), "rh": g("relative_humidity_2m"),
                    "precip": g("precipitation"), "pprob": g("precipitation_probability"),
                    "pressure": g("surface_pressure"), "wind": g("wind_speed_10m"),
                    "ghi": g("shortwave_radiation"), "direct": g("direct_radiation")})
    return out
