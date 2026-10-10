"""IMD 24-hour rainfall categories (published IMD terminology), applied to forecast totals.

These are categories on a forecast, not IMD warnings. Alerts start at 'heavy'.
"""

CATEGORIES: tuple[tuple[float, str], ...] = (   # lower bound mm/day, name
    (204.5, "extremely_heavy"), (115.6, "very_heavy"), (64.5, "heavy"),
    (15.6, "moderate"), (2.5, "light"), (0.1, "very_light"),
)
ALERT = ("heavy", "very_heavy", "extremely_heavy")
HINDI = {"extremely_heavy": "behad bhaari baarish", "very_heavy": "bahut bhaari baarish",
         "heavy": "bhaari baarish", "moderate": "madhyam baarish", "light": "halki baarish",
         "very_light": "boonda-baandi", "none": "baarish nahi"}


def category(mm: float) -> str:
    for lower, name in CATEGORIES:
        if round(mm, 1) >= lower:
            return name
    return "none"


def daily_rain(hourly: list[dict], day: str) -> dict:
    """hourly rows {'t': iso local, 'precip': mm, 'pprob': %} -> day summary."""
    rows = [r for r in hourly if r["t"][:10] == day]
    total = round(sum(r.get("precip") or 0 for r in rows), 1)
    wet = [int(r["t"][11:13]) for r in rows if (r.get("precip") or 0) >= 2.5]
    cat = category(total)
    return {"date": day, "total_mm": total, "category": cat, "alert": cat in ALERT,
            "max_prob": max((r.get("pprob") or 0 for r in rows), default=0),
            "wet_hours": wet}
