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
