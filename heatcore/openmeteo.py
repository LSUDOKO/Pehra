"""Open-Meteo clients (forecast + ERA5 archive). Free, no key, non-commercial.

Called only by the twice-daily ingest and offline scripts; a site lookup must
never call an external weather API.
"""

from datetime import UTC, datetime

import requests

from heatcore.wbgt import HourWeather

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_VARS = ("temperature_2m", "relative_humidity_2m", "surface_pressure",
               "wind_speed_10m", "shortwave_radiation", "direct_radiation")
EXTRA_VARS = ("precipitation", "precipitation_probability")  # forecast only
FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
TIMEOUT_S = 30


def _get(url: str, params: dict, session: requests.Session | None = None) -> dict:
    s = session or requests.Session()
    last: Exception | None = None
    for _ in range(3):
        try:
            r = s.get(url, params=params, timeout=TIMEOUT_S)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            last = e
    raise RuntimeError(f"Open-Meteo request failed: {last}") from last


def fetch_forecast(lat: float, lon: float, days: int = 4, session=None) -> dict:
    return _get(FORECAST_URL, {
        "latitude": lat, "longitude": lon, "hourly": ",".join(HOURLY_VARS + EXTRA_VARS),
        "wind_speed_unit": "ms", "timezone": "UTC", "forecast_days": days,
    }, session)


def fetch_archive(lat: float, lon: float, start: str, end: str, session=None) -> dict:
    """ERA5 reanalysis via Open-Meteo archive (CC BY 4.0). Dates are YYYY-MM-DD."""
    return _get(ARCHIVE_URL, {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "hourly": ",".join(HOURLY_VARS), "wind_speed_unit": "ms", "timezone": "UTC",
    }, session)


def parse_hourly(payload: dict) -> list[HourWeather]:
    """Turn an Open-Meteo hourly payload (UTC) into HourWeather rows; skip gaps."""
    h = payload["hourly"]
    rows = []
    for i, t in enumerate(h["time"]):
        vals = [h[v][i] for v in HOURLY_VARS[:5]]
        if any(v is None for v in vals):
            continue
        direct = h.get("direct_radiation", [None] * len(h["time"]))[i]
        rows.append(HourWeather(
            time_utc=datetime.fromisoformat(t).replace(tzinfo=UTC),
            temp_c=vals[0], rh_pct=vals[1], pressure_hpa=vals[2],
            wind_10m_ms=vals[3], ghi_wm2=vals[4], direct_wm2=direct,
        ))
    return rows


def fetch_daily_tmax(lat: float, lon: float, start: str, end: str, session=None) -> dict:
    """Daily max 2 m temperature (ERA5, local IST days) as {date: tmax_c}."""
    d = _get(ARCHIVE_URL, {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "daily": "temperature_2m_max", "timezone": "Asia/Kolkata",
    }, session)["daily"]
    return {t: v for t, v in zip(d["time"], d["temperature_2m_max"], strict=True) if v is not None}


def fetch_daily(lat: float, lon: float, start: str, end: str, variables: tuple[str, ...],
                session=None) -> dict[str, dict[str, float]]:
    """ERA5 daily variables (IST days) as {variable: {date: value}}."""
    d = _get(ARCHIVE_URL, {"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
                           "daily": ",".join(variables), "timezone": "Asia/Kolkata"}, session)["daily"]
    return {v: {t: x for t, x in zip(d["time"], d[v], strict=True) if x is not None} for v in variables}


def fetch_flood(lat: float, lon: float, *, days: int = 7, start: str | None = None, end: str | None = None,
                session=None) -> list[float | None]:
    """GloFAS daily river discharge (m3/s): forecast by default, or history with start/end."""
    params = {"latitude": lat, "longitude": lon, "daily": "river_discharge"}
    params |= {"start_date": start, "end_date": end} if start else {"forecast_days": days}
    return _get(FLOOD_URL, params, session)["daily"]["river_discharge"]


def geocode(name: str, session=None) -> dict | None:
    """Free Open-Meteo geocoding, India only: {'name', 'lat', 'lon', 'state'} or None."""
    tries = [name.strip()] + [part.strip() for part in name.split(",")[:1] if "," in name]
    for q in tries:
        r = _get(GEOCODE_URL, {"name": q, "count": 5, "countryCode": "IN", "language": "en"}, session)
        hits = [h for h in r.get("results") or [] if h.get("country_code", "IN") == "IN"]
        if hits:
            h = hits[0]
            return {"name": h["name"], "lat": h["latitude"], "lon": h["longitude"],
                    "state": h.get("admin1", "")}
    return None
