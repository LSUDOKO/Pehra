"""Daily-max normals (1991-2020) used by the recreated IMD rule.

Normal for a calendar day = mean daily max over the 30 years, within +/-7 days.
ERA5 stands in for IMD station normals; this is an approximation.
"""

from datetime import date, timedelta

WINDOW_DAYS = 7


def normal_for(day: date, tmax_by_date: dict[str, float]) -> float:
    targets = {((day + timedelta(days=k)).month, (day + timedelta(days=k)).day)
               for k in range(-WINDOW_DAYS, WINDOW_DAYS + 1)}
    vals = [v for t, v in tmax_by_date.items()
            if 1991 <= int(t[:4]) <= 2020 and (int(t[5:7]), int(t[8:10])) in targets]
    if not vals:
        raise ValueError("no normal-period data for that day")
    return round(sum(vals) / len(vals), 1)
