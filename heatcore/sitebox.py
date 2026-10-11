"""Pehra Site Box: turn one telemetry message into the state the box and the 3D twin show.

Measured WBGT (outdoor, ISO 7243 form): WBGT = 0.7*Tnw + 0.2*Tg + 0.1*Ta
- Tg: black-globe temperature (DS18B20 inside a matt-black ball)
- Tnw: natural wet bulb, approximated by the Stull (2011) psychrometric wet bulb from air temperature and
  humidity. In strong sun the real natural wet bulb runs slightly higher, so this is a lower bound.
Without a globe probe the server falls back to the forecast-radiation estimate (heatcore.sensor).
Levels and rest minutes use the same NIOSH moderate-work limit and 1 C bands as the site plans.
"""

import math
from datetime import datetime

from heatcore.bands import band_for
from heatcore.niosh import rel
from heatcore.personal import LEVELS, level_for
from heatcore.sensor import DRAIN_HIGH_CM, TANK_LOW_PCT, drain_level_cm, tank_percent

LIMIT_C = round(rel(300), 1)  # moderate work, acclimatised
COLORS = ("#2FB344", "#FFC20E", "#FF8A1F", "#E8282B", "#A266B0")
LABELS = ("KAM", "SAAVDHAAN", "ZYADA", "BAHUT ZYADA", "KHATARNAK")
FAN_FROM_LEVEL = 2          # mist fan from 'zyada'
PUMP_OFF_PCT = 90           # refill until 90% (hysteresis with TANK_LOW_PCT)
LIGHT_MAX_RAW = 4095


def stull_wet_bulb(t_c: float, rh: float) -> float:
    """Psychrometric wet bulb (Stull 2011), valid ~5-99% RH, -20..50 C."""
    rh = min(max(rh, 5.0), 99.0)
    return (t_c * math.atan(0.151977 * math.sqrt(rh + 8.313659)) + math.atan(t_c + rh)
            - math.atan(rh - 1.676331) + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh) - 4.686035)


def measured_wbgt(t_c: float, rh: float, globe_c: float) -> float:
    return round(0.7 * stull_wet_bulb(t_c, rh) + 0.2 * globe_c + 0.1 * t_c, 1)


def _fit(s: str) -> str:
    return s[:21]


def evaluate(r: dict, *, tank_height_cm: float = 120, drain_mount_cm: float = 100,
             forecast_wbgt_c: float | None = None, fallback_wbgt_c: float | None = None,
             prev_pump: bool = False, sos_recent: bool = False, now: datetime | None = None,
             box_id: str = "", site_name: str = "") -> dict:
    """Pure function: telemetry dict -> state dict (docs/SITEBOX_CONTRACT.md)."""
    now = now or datetime.now()
    t, rh = float(r["temp_c"]), float(r["rh"])
    if not (-10 <= t <= 60 and 0 <= rh <= 100):
        raise ValueError("air reading out of range")
    globe = r.get("globe_c")
    if globe is not None and -10 <= float(globe) <= 90:
        wbgt = measured_wbgt(t, rh, float(globe))
        source = "globe"
    elif fallback_wbgt_c is not None:
        wbgt, source = round(fallback_wbgt_c, 1), "forecast_radiation"
    else:
        wbgt, source = round(stull_wet_bulb(t, rh) * 0.7 + 0.3 * t, 1), "shade_estimate"
    e = round(wbgt - LIMIT_C, 1)
    idx = level_for(e)
    rest, _ = band_for(e)
    stop = rest == 60
    aaram = stop or (rest > 0 and now.minute >= 60 - rest)

    readings = {"temp_c": round(t, 1), "rh": round(rh), "globe_c": None if globe is None else round(float(globe), 1)}
    light = r.get("light_raw")
    readings["light_pct"] = None if light is None else int(round(min(max(float(light), 0), LIGHT_MAX_RAW) / LIGHT_MAX_RAW * 100))
    tank = drain = None
    if r.get("tank_distance_cm") is not None:
        tank = tank_percent(float(r["tank_distance_cm"]), tank_height_cm)
    if r.get("drain_distance_cm") is not None:
        drain = drain_level_cm(float(r["drain_distance_cm"]), drain_mount_cm)
    readings["tank_pct"], readings["drain_cm"] = tank, drain

    pump = prev_pump
    if tank is not None:
        if tank < TANK_LOW_PCT:
            pump = True
        elif tank >= PUMP_OFF_PCT:
            pump = False
    sos = bool(r.get("sos")) or sos_recent

    alerts = []
    if tank is not None and tank < TANK_LOW_PCT:
        alerts.append("tank_low")
    if drain is not None and drain >= DRAIN_HIGH_CM:
        alerts.append("waterlogging")
    if forecast_wbgt_c is not None and wbgt - forecast_wbgt_c >= 1.0:
        alerts.append("hotter_than_forecast")
    if sos:
        alerts.append("sos")

    line3 = "KAAM BAND" if stop else ("AARAM ABHI" if aaram else ("SOS BHEJA" if sos else "KAAM CHALU"))
    line4 = " ".join(x for x in (f"Tank {tank}%" if tank is not None else "", f"Naali {drain:g}cm" if drain is not None else "") if x)
    return {"box_id": box_id, "site_name": site_name, "updated_at": now.isoformat(timespec="seconds"),
            "readings": readings, "wbgt_c": wbgt, "wbgt_source": source, "forecast_wbgt_c": forecast_wbgt_c,
            "limit_c": LIMIT_C, "level": LEVELS[idx], "level_index": idx, "level_label": LABELS[idx],
            "color": COLORS[idx], "rest_minutes": rest, "aaram_now": aaram, "stop_now": stop,
            "fan_on": idx >= FAN_FROM_LEVEL, "pump_on": pump, "sos_active": sos, "alerts": alerts,
            "display": [_fit(f"WBGT {wbgt:.1f}C {LABELS[idx]}"), _fit(f"{rest} min aaram/ghanta"), _fit(line3),
                        _fit(line4 or "Pehra Site Box")]}
