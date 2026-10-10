"""Personal and family heat risk ("Garmi Saathi"), built on the same WBGT engine.

Project rule (documented in docs/PLAN_ALGORITHM.md, not a medical assessment):
- Healthy adults outdoors: WBGT in sun vs NIOSH REL for light activity (180 W).
- Vulnerable members (65+, under 5, pregnant, chronic illness): the stricter RAL for light activity.
- Household member who works outdoors: WBGT in sun vs REL for moderate work (300 W).
Exceedance E = (WBGT + margin) - limit maps to five levels with the same 1 C edges as the work bands.
"""

from dataclasses import asdict, dataclass

from heatcore.niosh import ral, rel
from heatcore.plan import HourHeat

LEVELS = ("kam", "saavdhaan", "zyada", "bahut_zyada", "khatarnak")
LEVEL_HI = {"kam": "kam khatra", "saavdhaan": "saavdhaan", "zyada": "zyada khatra",
            "bahut_zyada": "bahut zyada khatra", "khatarnak": "khatarnak"}
LEVEL_EN = {"kam": "lower risk", "saavdhaan": "caution", "zyada": "high", "bahut_zyada": "very high",
            "khatarnak": "extreme"}
DAY_HOURS = range(6, 20)     # 06:00-19:59 local
AVOID_FROM_LEVEL = 3         # 'bahut_zyada' and above: stay indoors / avoid going out
GOOD_MAX_LEVEL = 1           # 'saavdhaan' or lower: better time for errands


@dataclass
class Household:
    adults: int = 1
    elderly: int = 0
    young_children: int = 0
    pregnant: int = 0
    chronic: int = 0
    works_outdoors: bool = False

    def __post_init__(self):
        if min(self.adults, self.elderly, self.young_children, self.pregnant, self.chronic) < 0:
            raise ValueError("counts must be >= 0")

    @property
    def vulnerable(self) -> int:
        return self.elderly + self.young_children + self.pregnant + self.chronic


def level_for(exceedance_c: float) -> int:
    e = round(exceedance_c, 2)
    for i, upper in enumerate((0.0, 1.0, 2.0, 3.0)):
        if e <= upper:
            return i
    return 4


def group_limits(h: Household) -> dict[str, float]:
    out = {"adults": round(rel(180), 1)}
    if h.vulnerable:
        out["vulnerable"] = round(ral(180), 1)
    if h.works_outdoors:
        out["outdoor_worker"] = round(rel(300), 1)
    return out


def _ranges(hours: list[int]) -> list[tuple[int, int]]:
    out: list[list[int]] = []
    for hr in sorted(hours):
        if out and out[-1][1] == hr:
            out[-1][1] = hr + 1
        else:
            out.append([hr, hr + 1])
    return [(a, b) for a, b in out]


def personal_forecast(heat: list[HourHeat], household: Household, margin_c: float = 1.0) -> dict:
    """Hourly levels per group for the daytime hours in `heat` (one local day)."""
    limits = group_limits(household)
    day = [h for h in heat if h.time_local.hour in DAY_HOURS]
    if not day:
        raise ValueError("no daytime hours in forecast")
    groups = {}
    for g, lim in limits.items():
        hourly = [{"hour": h.time_local.hour, "wbgt": h.wbgt_sun,
                   "level": level_for(h.wbgt_sun + margin_c - lim)} for h in day]
        peak = max(x["level"] for x in hourly)
        groups[g] = {"limit_c": lim, "peak_level": LEVELS[peak], "hourly": hourly,
                     "avoid": _ranges([x["hour"] for x in hourly if x["level"] >= AVOID_FROM_LEVEL])}
    strict = groups.get("vulnerable") or groups["adults"]
    better = _ranges([x["hour"] for x in strict["hourly"] if x["level"] <= GOOD_MAX_LEVEL])
    return {"date": day[0].time_local.date().isoformat(), "household": asdict(household),
            "margin_c": margin_c, "groups": groups, "better_windows": better,
            "peak_wbgt_sun": max(h.wbgt_sun for h in day),
            "overall_level": max((g["peak_level"] for g in groups.values()), key=LEVELS.index)}
