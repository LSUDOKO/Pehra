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


def normals_by_mmdd(values_by_date: dict[str, float]) -> dict[str, float]:
    """1991-2020 normal for every calendar day ('MM-DD'), +/-7-day window. Works for tmax or tmin."""
    from collections import defaultdict

    by_md: dict[tuple[int, int], list[float]] = defaultdict(list)
    for t, v in values_by_date.items():
        if v is not None and 1991 <= int(t[:4]) <= 2020:
            by_md[(int(t[5:7]), int(t[8:10]))].append(v)
    out = {}
    ref = date(2020, 1, 1)  # leap year, so 29 Feb gets a normal too
    for i in range(366):
        d = ref + timedelta(days=i)
        vals = []
        for k in range(-WINDOW_DAYS, WINDOW_DAYS + 1):
            w = d + timedelta(days=k)
            vals += by_md.get((w.month, w.day), [])
        if vals:
            out[f"{d.month:02d}-{d.day:02d}"] = round(sum(vals) / len(vals), 1)
    return out
