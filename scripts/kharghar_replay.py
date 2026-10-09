"""Kharghar replay: what would Invisible Heat have said on 16 April 2023?

Runs the same engine on ERA5 reanalysis (Open-Meteo archive) for Kharghar,
Navi Mumbai, and checks the recreated IMD heatwave rule for that day.

    uv run python scripts/kharghar_replay.py [--json out.json]
"""

import argparse
import json
from datetime import date, datetime, timedelta

from heatcore.cities import get_city
from heatcore.climatology import normal_for
from heatcore.daily import Crew, ForecastMeta, build_daily_plan
from heatcore.heat import compute_heat, for_date
from heatcore.imd_rule import day_level, district_flags
from heatcore.niosh import limits
from heatcore.openmeteo import fetch_archive, fetch_daily_tmax, parse_hourly

DAY = date(2023, 4, 16)
EVENT_HOURS = range(10, 14)  # ceremony window in IST, per news reports (see 13-sources.md)


def run() -> dict:
    city = get_city("kharghar")
    rows = parse_hourly(fetch_archive(city.lat, city.lon, DAY.isoformat(), DAY.isoformat()))
    heat = for_date(compute_heat(rows, city.lat, city.lon), DAY.isoformat())

    tmax = fetch_daily_tmax(city.lat, city.lon, "1991-01-01", "2020-12-31")
    near = fetch_daily_tmax(city.lat, city.lon, (DAY - timedelta(days=1)).isoformat(),
                            (DAY + timedelta(days=1)).isoformat())
    days = sorted(near)
    normals = [normal_for(date.fromisoformat(d), tmax) for d in days]
    flags = district_flags([[near[d] for d in days]], [normals], city.region, min_cells=1)
    i = days.index(DAY.isoformat())

    # The app plans from a forecast issued the evening before; ERA5 stands in for it.
    issued = datetime(2023, 4, 15, 12, 0)
    plan = build_daily_plan(heat, Crew(headcount=100), ForecastMeta("ERA5 reanalysis", issued),
                            datetime(2023, 4, 15, 19, 0), site_id="kharghar-replay",
                            site_name=city.name)
    return {
        "date": DAY.isoformat(), "place": city.name,
        "imd": {"tmax_c": near[DAY.isoformat()], "normal_c": normals[i],
                "departure_c": round(near[DAY.isoformat()] - normals[i], 1),
                "region": city.region,
                "day_level": str(day_level(near[DAY.isoformat()], normals[i], city.region)),
                "heatwave_declared": flags[i]},
        "limits": {w: limits(w) for w in ("light", "moderate", "heavy")},
        "hours": [{"hour": h.time_local.hour, "wbgt_sun": h.wbgt_sun, "wbgt_shade": h.wbgt_shade}
                  for h in heat],
        "plan": plan,
    }


def print_report(r: dict) -> None:
    rel_mod = r["limits"]["moderate"]["rel_c"]
    print(f"Invisible Heat replay - {r['place']} - {r['date']}  (ERA5 reanalysis)\n")
    imd = r["imd"]
    print(f"IMD rule (recreated): Tmax {imd['tmax_c']} C, normal {imd['normal_c']} C, "
          f"departure {imd['departure_c']} C, region {imd['region']}")
    print(f"  -> heatwave declared: {'YES' if imd['heatwave_declared'] else 'NO'}\n")
    print(f"NIOSH REL moderate work: {rel_mod} C   (heavy: {r['limits']['heavy']['rel_c']} C)\n")
    print("Hour  WBGT sun  WBGT shade  sun-REL(mod)  plan rest/h  status")
    by_hour = {h["hour"]: h for h in r["plan"]["plans"]["moderate"]["hours"]}
    for h in r["hours"]:
        p = by_hour.get(h["hour"])
        mark = " <- event" if h["hour"] in EVENT_HOURS else ""
        rest = f"{p['rest_minutes']:>3} min  {p['status']}" if p else "   -"
        print(f"{h['hour']:02d}:00  {h['wbgt_sun']:>7.1f}  {h['wbgt_shade']:>9.1f}  "
              f"{h['wbgt_sun'] - rel_mod:>+10.1f}  {rest}{mark}")
    pl = r["plan"]
    if pl["stop_from"] is not None:
        print(f"\nPlan the app would have sent: stop work {pl['stop_from']}:00-{pl['stop_to']}:00")
    print("\nCaveats: ERA5 is a ~25 km reanalysis and smooths extremes; IMD rule approximated.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write full result to this path")
    a = ap.parse_args()
    result = run()
    print_report(result)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(result, f, indent=2, default=str)
