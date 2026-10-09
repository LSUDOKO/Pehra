"""Solar geometry and radiation split (no external deps beyond numpy).

Zenith angle uses the NOAA solar position equations (accurate to ~0.01 deg,
plenty for hourly WBGT). Erbs et al. (1982) splits global horizontal
radiation into direct and diffuse when the forecast doesn't provide it.
"""

import math
from datetime import UTC, datetime

SOLAR_CONSTANT = 1361.0  # W/m2


def cos_zenith(lat: float, lon: float, when_utc: datetime) -> float:
    """Cosine of the solar zenith angle at a UTC instant (clipped at 0)."""
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=UTC)
    t = when_utc.astimezone(UTC)
    doy = t.timetuple().tm_yday
    hour = t.hour + t.minute / 60 + t.second / 3600
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
            - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                       - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    true_solar_min = hour * 60 + eqtime + 4 * lon
    hour_angle = math.radians(true_solar_min / 4 - 180)
    phi = math.radians(lat)
    cz = math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(hour_angle)
    return max(0.0, cz)


def extraterrestrial_horizontal(cossza: float, when_utc: datetime) -> float:
    doy = when_utc.timetuple().tm_yday
    e0 = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    return SOLAR_CONSTANT * e0 * max(cossza, 0.0)


def erbs_direct_fraction(ghi: float, cossza: float, when_utc: datetime) -> float:
    """Direct-beam fraction of global horizontal radiation (Erbs 1982)."""
    if ghi <= 0 or cossza <= 0.01:
        return 0.0
    i0h = extraterrestrial_horizontal(cossza, when_utc)
    kt = min(max(ghi / i0h, 0.0), 1.0) if i0h > 0 else 0.0
    if kt <= 0.22:
        diffuse = 1.0 - 0.09 * kt
    elif kt <= 0.80:
        diffuse = 0.9511 - 0.1604 * kt + 4.388 * kt**2 - 16.638 * kt**3 + 12.336 * kt**4
    else:
        diffuse = 0.165
    return min(max(1.0 - diffuse, 0.0), 0.9)


def cos_zenith_array(lat: float, lon: float, times_utc):
    """Vectorised cos_zenith for a numpy array of datetime64 (UTC). Same NOAA equations."""
    import numpy as np

    t = np.asarray(times_utc, dtype="datetime64[s]")
    doy = (t.astype("datetime64[D]") - t.astype("datetime64[Y]")).astype(int) + 1
    hour = (t - t.astype("datetime64[D]")).astype(int) / 3600.0
    g = 2 * np.pi / 365 * (doy - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
                       - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    ha = np.radians((hour * 60 + eqtime + 4 * lon) / 4 - 180)
    phi = np.radians(lat)
    cz = np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.cos(ha)
    return np.clip(cz, 0.0, None)
