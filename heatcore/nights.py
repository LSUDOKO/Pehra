"""Warm nights, recreated from IMD's definition (considered only when the day's max is >= 40 C):
warm night if the minimum temperature departs 4.5-6.4 C above normal, very warm if more than 6.4 C.
Hot nights stop the body recovering from daytime heat; most Indian heat plans ignore them.
"""


def warm_night(tmax_c: float, tmin_c: float, tmin_normal_c: float) -> str:
    if tmax_c < 40.0:
        return "none"
    dep = round(tmin_c - tmin_normal_c, 2)
    if dep > 6.4:
        return "very_warm"
    if dep >= 4.5:
        return "warm"
    return "none"


def night_summary(hourly: list[dict], day: str) -> dict:
    """Night after `day`: 20:00 that day to 06:00 next morning; uses 'temp' in hourly rows."""
    from datetime import date, timedelta

    nxt = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    rows = [r for r in hourly if (r["t"][:10] == day and int(r["t"][11:13]) >= 20)
            or (r["t"][:10] == nxt and int(r["t"][11:13]) < 6)]
    temps = [r["temp"] for r in rows if r.get("temp") is not None]
    day_rows = [r["temp"] for r in hourly if r["t"][:10] == day and r.get("temp") is not None]
    return {"night_min_c": round(min(temps), 1) if temps else None,
            "day_max_c": round(max(day_rows), 1) if day_rows else None}
