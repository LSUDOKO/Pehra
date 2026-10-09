"""Find the coolest contiguous working window for a task (PLAN_ALGORITHM step 6)."""

from itertools import groupby

from heatcore.bands import STATUS_ORDER, band_for
from heatcore.niosh import ral, rel
from heatcore.plan import WORKDAY_END_HOUR, WORKDAY_START_HOUR, HourHeat
from heatcore.workload import Workload, metabolic_rate


def find_window(
    heat: list[HourHeat],
    duration_hours: int,
    workload: Workload | str = Workload.HEAVY,
    *,
    acclimatised: bool = True,
    margin_c: float = 1.0,
) -> dict:
    """Lowest max-exceedance window of `duration_hours` within one workday.

    `flagged` is True when even the best window is worse than 'caution'.
    """
    if not 1 <= duration_hours <= WORKDAY_END_HOUR - WORKDAY_START_HOUR:
        raise ValueError("duration must fit inside one workday")
    m = metabolic_rate(workload)
    limit = rel(m) if acclimatised else ral(m)
    work = [h for h in heat if WORKDAY_START_HOUR <= h.time_local.hour < WORKDAY_END_HOUR]
    best = None
    for _, day_iter in groupby(work, key=lambda h: h.time_local.date()):
        day = list(day_iter)
        for i in range(len(day) - duration_hours + 1):
            win = day[i:i + duration_hours]
            if any(b.time_local.hour != a.time_local.hour + 1 for a, b in zip(win, win[1:], strict=False)):
                continue
            worst = round(max(h.wbgt_sun for h in win) + margin_c - limit, 1)
            if best is None or worst < best[0]:
                best = (worst, win)
    if best is None:
        raise ValueError("no window of that length in the forecast")
    worst, win = best
    _, status = band_for(worst)
    return {
        "date": win[0].time_local.date().isoformat(),
        "start_hour": win[0].time_local.hour,
        "end_hour": win[-1].time_local.hour + 1,
        "max_wbgt_planning": round(max(h.wbgt_sun for h in win) + margin_c, 1),
        "limit_c": round(limit, 1),
        "max_exceedance_c": worst,
        "status": status,
        "flagged": STATUS_ORDER[status] > STATUS_ORDER["caution"],
    }
