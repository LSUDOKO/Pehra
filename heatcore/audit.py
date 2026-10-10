"""Invisible Heat Audit: days when WBGT crossed the NIOSH limit but the recreated IMD
heatwave rule would not have declared a heatwave.

Definitions (documented in the README and on the audit page):
- Danger day: WBGT in SHADE during working hours (06-19 IST) exceeded the NIOSH REL for
  moderate work (28.2 C) for at least one hour. Shade is the conservative choice; sun counts
  are reported alongside.
- Heatwave day: recreated IMD rule on ERA5 daily max (single grid cell per city; the
  "2 or more stations" condition cannot be applied to one cell).
- Invisible heat day: danger day AND not a heatwave day.
ERA5 smooths extremes, so every count is a minimum.
"""

from collections import defaultdict
from datetime import date

from heatcore.climatology import normal_for, normals_by_mmdd
from heatcore.imd_rule import district_flags
from heatcore.nights import warm_night
from heatcore.niosh import rel
from heatcore.rain import ALERT as RAIN_ALERT
from heatcore.rain import category
from heatcore.workload import metabolic_rate

LIMIT_C = round(rel(metabolic_rate("moderate")), 1)
HOT_SEASON_MONTHS = (3, 4, 5, 6)


def daily_max_work_wbgt(hours_ist: list[tuple[str, int, float, float]]) -> dict[str, tuple[float, float]]:
    """(date, hour, sun, shade) rows -> {date: (max_sun, max_shade)} over 06-19 IST."""
    out: dict[str, list[float]] = defaultdict(lambda: [-99.0, -99.0])
    for d, h, sun, shade in hours_ist:
        if 6 <= h < 19:
            m = out[d]
            m[0], m[1] = max(m[0], sun), max(m[1], shade)
    return {d: (round(v[0], 1), round(v[1], 1)) for d, v in out.items()}


def audit_city(wbgt_by_day: dict[str, tuple[float, float]], tmax_by_day: dict[str, float],
               climatology: dict[str, float], region: str, tmin_by_day: dict[str, float] | None = None,
               tmin_climatology: dict[str, float] | None = None,
               rain_by_day: dict[str, float] | None = None) -> list[dict]:
    days = sorted(set(wbgt_by_day) & set(tmax_by_day))
    normals = [normal_for(date.fromisoformat(d), climatology) for d in days]
    hw = district_flags([[tmax_by_day[d] for d in days]], [normals], region, min_cells=1)
    tmin_norm = normals_by_mmdd(tmin_climatology) if tmin_climatology else {}
    rows = []
    for d, n, flag in zip(days, normals, hw, strict=True):
        sun, shade = wbgt_by_day[d]
        tmin = (tmin_by_day or {}).get(d)
        night = (warm_night(tmax_by_day[d], tmin, tmin_norm[d[5:]])
                 if tmin is not None and d[5:] in tmin_norm else "none")
        rain = (rain_by_day or {}).get(d)
        rows.append({"date": d, "tmax_c": tmax_by_day[d], "normal_c": n, "imd_heatwave": flag,
                     "tmin_c": tmin, "warm_night": night != "none", "rain_mm": rain,
                     "heavy_rain": rain is not None and category(rain) in RAIN_ALERT,
                     "wbgt_sun_max": sun, "wbgt_shade_max": shade,
                     "danger_shade": shade > LIMIT_C, "danger_sun": sun > LIMIT_C,
                     "invisible_shade": shade > LIMIT_C and not flag,
                     "invisible_sun": sun > LIMIT_C and not flag,
                     "outside_mar_jun": int(d[5:7]) not in HOT_SEASON_MONTHS})
    return rows


def summarise(rows: list[dict]) -> dict:
    def count(key, extra=lambda r: True):
        return sum(1 for r in rows if r[key] and extra(r))
    return {"days": len(rows), "heatwave_days": count("imd_heatwave"),
            "danger_days_shade": count("danger_shade"), "danger_days_sun": count("danger_sun"),
            "invisible_days_shade": count("invisible_shade"),
            "invisible_days_sun": count("invisible_sun"),
            "invisible_shade_outside_mar_jun": count("invisible_shade", lambda r: r["outside_mar_jun"]),
            "warm_nights": sum(1 for r in rows if r.get("warm_night")),
            "heavy_rain_days": sum(1 for r in rows if r.get("heavy_rain")),
            "limit_c": LIMIT_C}
