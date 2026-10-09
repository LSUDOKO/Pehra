"""The AI may make a plan stricter, never looser."""

from heatcore.plan import Plan


class LooserPlanError(ValueError):
    pass


def loosened_hours(base: Plan, candidate: Plan) -> list[int]:
    """Hours where the candidate gives less rest than the base plan (or drops the hour)."""
    cand = {h.hour: h.rest_minutes for h in candidate.hours}
    return [h.hour for h in base.hours if cand.get(h.hour, -1) < h.rest_minutes]


def assert_not_looser(base: Plan, candidate: Plan) -> None:
    bad = loosened_hours(base, candidate)
    if bad:
        raise LooserPlanError(f"plan loosened at hours {bad}")


def direction(base: Plan, candidate: Plan) -> str:
    """'looser' if any hour has less rest, else 'stricter' (or 'same')."""
    if loosened_hours(base, candidate):
        return "looser"
    b = {h.hour: h.rest_minutes for h in base.hours}
    return "stricter" if any(h.rest_minutes > b.get(h.hour, 0) for h in candidate.hours) else "same"


def stricter_hours(old: dict, new: dict, from_hour: int, workload: str = "moderate") -> list[int]:
    """Remaining hours (>= from_hour) where the new daily plan needs more rest than the old one."""
    before = {h["hour"]: h["rest_minutes"] for h in old["plans"][workload]["hours"]}
    return [h["hour"] for h in new["plans"][workload]["hours"]
            if h["hour"] >= from_hour and h["rest_minutes"] > before.get(h["hour"], 0)]
