"""Outdoor WBGT in sun and shade via thermofeel's Liljegren (2008) model.

Same physics as OSHA's online WBGT calculator. Shade = same call with
solar radiation set to zero. Do not use simplified (BoM) WBGT here.
"""

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import thermofeel

from heatcore.solar import cos_zenith, erbs_direct_fraction


@dataclass(frozen=True)
class HourWeather:
    time_utc: datetime
    temp_c: float
    rh_pct: float
    pressure_hpa: float
    wind_10m_ms: float
    ghi_wm2: float
    direct_wm2: float | None = None  # direct horizontal, if the source provides it


def _wbgt_c(t_c, rh, p, va, ssrd, fdir, cossza) -> float:
    k = thermofeel.calculate_wbgt_liljegren(
        np.array([t_c + 273.15]), np.array([rh]), np.array([p]), np.array([va]),
        np.array([ssrd]), np.array([fdir]), np.array([cossza]),
    )
    return float(k[0]) - 273.15


def direct_fraction(h: HourWeather, cossza: float) -> float:
    if h.ghi_wm2 <= 0 or cossza <= 0:
        return 0.0
    if h.direct_wm2 is not None:
        return min(max(h.direct_wm2 / h.ghi_wm2, 0.0), 0.9)
    return erbs_direct_fraction(h.ghi_wm2, cossza, h.time_utc)


def wbgt_hour(h: HourWeather, lat: float, lon: float) -> dict[str, float]:
    """Return {'wbgt_sun', 'wbgt_shade'} in deg C, rounded to 0.1."""
    cz = cos_zenith(lat, lon, h.time_utc)
    fdir = direct_fraction(h, cz)
    sun = _wbgt_c(h.temp_c, h.rh_pct, h.pressure_hpa, h.wind_10m_ms, max(h.ghi_wm2, 0), fdir, cz)
    shade = _wbgt_c(h.temp_c, h.rh_pct, h.pressure_hpa, h.wind_10m_ms, 0.0, 0.0, cz)
    return {"wbgt_sun": round(sun, 1), "wbgt_shade": round(shade, 1)}


def wbgt_series(hours: list[HourWeather], lat: float, lon: float) -> list[dict]:
    return [{"time_utc": h.time_utc.isoformat(), **wbgt_hour(h, lat, lon)} for h in hours]
