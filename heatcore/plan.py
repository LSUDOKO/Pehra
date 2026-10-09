"""Hour-by-hour work-rest plan (see docs/PLAN_ALGORITHM.md).

Deterministic: same inputs -> same plan. Every number a user sees comes from here.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime

from heatcore.bands import band_for
from heatcore.niosh import ral, rel
from heatcore.workload import Workload, metabolic_rate

WORKDAY_START_HOUR = 6   # local time, inclusive
WORKDAY_END_HOUR = 19    # local time, exclusive


@dataclass(frozen=True)
class HourHeat:
    time_local: datetime   # start of the hour, local (IST) time
    wbgt_sun: float
    wbgt_shade: float


@dataclass
class PlanHour:
    hour: int
    wbgt: float
    wbgt_planning: float
    limit_c: float
    exceedance_c: float
    rest_minutes: int
    work_minutes: int
    status: str


@dataclass
class Plan:
    date: str
    workload: str
    acclimatised: bool
    exposure: str
    margin_c: float
    limit_c: float
    hours: list[PlanHour] = field(default_factory=list)
    stop_from: int | None = None
    stop_to: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def build_plan(
    heat: list[HourHeat],
    workload: Workload | str = Workload.MODERATE,
    *,
    acclimatised: bool = True,
    margin_c: float = 1.0,
    shade: bool = False,
) -> Plan:
    if margin_c < 0:
        raise ValueError("margin must be >= 0; a plan may never be loosened")
    if not heat:
        raise ValueError("no heat data for the plan")
    m = metabolic_rate(workload)
    limit = rel(m) if acclimatised else ral(m)
    day = heat[0].time_local.date().isoformat()
    plan = Plan(date=day, workload=str(Workload(workload)), acclimatised=acclimatised,
                exposure="shade" if shade else "sun", margin_c=margin_c, limit_c=round(limit, 1))
    for h in heat:
        if not WORKDAY_START_HOUR <= h.time_local.hour < WORKDAY_END_HOUR:
            continue
        w = h.wbgt_shade if shade else h.wbgt_sun
        w_plan = round(w + margin_c, 1)
        e = round(w_plan - limit, 1)
        rest, status = band_for(e)
        plan.hours.append(PlanHour(h.time_local.hour, round(w, 1), w_plan, round(limit, 1),
                                   e, rest, 60 - rest, status))
    window = stop_window(plan.hours)
    if window:
        plan.stop_from, plan.stop_to = window
    return plan


def stop_window(hours: list[PlanHour]) -> tuple[int, int] | None:
    """Longest run of consecutive 'stop' hours as (from_hour, to_hour), to exclusive."""
    best: tuple[int, int] | None = None
    start = end = None
    for h in hours:
        if h.status == "stop" and start is not None and h.hour == end:
            end = h.hour + 1
        elif h.status == "stop":
            start, end = h.hour, h.hour + 1
        else:
            start = end = None
            continue
        if best is None or end - start > best[1] - best[0]:
            best = (start, end)
    return best
