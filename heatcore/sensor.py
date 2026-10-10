"""Site sensors: measured temperature/humidity -> site WBGT; ultrasonic level -> tank or drain level.

A DHT22-class sensor gives air temperature and humidity at the site. Wind and sunlight come from the
forecast for that hour, so the result is a *site-corrected* WBGT: it captures the hotter, more humid
air around tin roofs and concrete that a 11-25 km grid misses.
"""

from datetime import datetime

from heatcore.wbgt import HourWeather, wbgt_hour

HOTTER_THAN_FORECAST_C = 1.0
TANK_LOW_PCT = 20
DRAIN_HIGH_CM = 30


def site_wbgt(when_utc: datetime, lat: float, lon: float, temp_c: float, rh_pct: float, wx: dict) -> dict:
    """wx: forecast row for the hour with pressure, wind, ghi, direct."""
    if not (-10 <= temp_c <= 60 and 0 <= rh_pct <= 100):
        raise ValueError("sensor reading out of range")
    h = HourWeather(when_utc, temp_c, rh_pct, wx.get("pressure", 1005.0), wx.get("wind", 1.0),
                    wx.get("ghi", 0.0), wx.get("direct"))
    return wbgt_hour(h, lat, lon)


def compare(measured_sun: float, forecast_sun: float) -> dict:
    diff = round(measured_sun - forecast_sun, 1)
    return {"measured": measured_sun, "forecast": forecast_sun, "diff_c": diff,
            "hotter": diff >= HOTTER_THAN_FORECAST_C}


def tank_percent(distance_cm: float, tank_height_cm: float) -> int:
    """Ultrasonic sensor at the tank top: distance to water surface -> % full."""
    if tank_height_cm <= 0:
        raise ValueError("tank height must be positive")
    return int(round(max(0.0, min(1.0, (tank_height_cm - distance_cm) / tank_height_cm)) * 100))


def drain_level_cm(distance_cm: float, mount_height_cm: float) -> float:
    """Sensor above a drain: water depth = mount height - distance to the surface."""
    return round(max(0.0, mount_height_cm - distance_cm), 1)
