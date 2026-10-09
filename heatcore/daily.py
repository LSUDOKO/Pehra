"""Assemble one site's daily plan: crew plans, new-worker schedule, water.

The output dict is the single source for every message, poster and record.
"""

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime

from heatcore.acclimatisation import new_worker_fraction, reduced_work_minutes, uses_ral
from heatcore.margin import planning_margin
from heatcore.plan import HourHeat, Plan, build_plan
from heatcore.water import BUFFER, CAN_LITRES, water_plan


@dataclass
class Crew:
    headcount: int = 0
    heavy_count: int = 0
    new_count: int = 0
    new_day: int = 1

    def __post_init__(self):
        if min(self.headcount, self.heavy_count, self.new_count) < 0:
            raise ValueError("crew counts must be >= 0")
        if self.heavy_count + self.new_count > self.headcount:
            raise ValueError("heavy + new workers cannot exceed headcount")


@dataclass
class ForecastMeta:
    model: str
    issued_at: datetime


def _summary(plan: Plan) -> list[dict]:
    """Collapse consecutive hours with the same rest minutes into periods."""
    periods: list[dict] = []
    for h in plan.hours:
        last = periods[-1] if periods else None
        if last and last["rest_minutes"] == h.rest_minutes and last["to"] == h.hour:
            periods[-1]["to"] = h.hour + 1
        else:
            periods.append({"from": h.hour, "to": h.hour + 1, "rest_minutes": h.rest_minutes,
                            "status": h.status})
    return periods


def build_daily_plan(
    heat: list[HourHeat],
    crew: Crew,
    forecast: ForecastMeta,
    now: datetime,
    *,
    site_id: str = "",
    site_name: str = "",
) -> dict:
    margin, stale = planning_margin(forecast.issued_at, now)
    main = build_plan(heat, "moderate", margin_c=margin)
    heavy = build_plan(heat, "heavy", margin_c=margin) if crew.heavy_count else None

    new = None
    if crew.new_count:
        base = build_plan(heat, "moderate", acclimatised=not uses_ral(crew.new_day),
                          margin_c=margin)
        frac = new_worker_fraction(crew.new_day)
        new = {"count": crew.new_count, "day": crew.new_day, "fraction": frac,
               "work_minutes": reduced_work_minutes([h.work_minutes for h in base.hours], frac),
               "hours": [h.hour for h in base.hours], "limit_c": base.limit_c}

    regular = crew.headcount - crew.heavy_count - crew.new_count
    water = water_plan([h.work_minutes for h in main.hours], regular)
    if heavy:
        hw = water_plan([h.work_minutes for h in heavy.hours], crew.heavy_count)
        water["litres"] = round(water["litres"] + hw["litres"], 1)
    if new:
        nw = water_plan(new["work_minutes"], crew.new_count)
        water["litres"] = round(water["litres"] + nw["litres"], 1)
    water["headcount"] = crew.headcount
    water["cans_20l"] = math.ceil(round(water["litres"] * (1 + BUFFER), 6) / CAN_LITRES)
    water.pop("cups_per_worker", None)

    out = {
        "site_id": site_id, "site_name": site_name, "date": main.date,
        "forecast_model": forecast.model, "forecast_issued": forecast.issued_at.isoformat(),
        "generated_at": now.isoformat(), "stale": stale, "margin_c": margin,
        "crew": asdict(crew),
        "stop_from": main.stop_from, "stop_to": main.stop_to,
        "heavy_stop": ({"from": heavy.stop_from, "to": heavy.stop_to} if heavy else None),
        "plans": {"moderate": main.to_dict(), **({"heavy": heavy.to_dict()} if heavy else {})},
        "rest_summary": _summary(main),
        "new_workers": new, "water": water,
        "peak_wbgt": max((h.wbgt for h in main.hours), default=None),
    }
    out["plan_hash"] = plan_hash(out)
    return out


def plan_hash(plan: dict) -> str:
    body = {k: v for k, v in plan.items() if k not in ("plan_hash", "generated_at")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()
