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
        "latitude": lat, "longitude": lon, "hourly": ",".join(HOURLY_VARS),
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
