"""NIOSH water plan: one cup (~240 ml) per 15-20 min of work, max 6 cups/hour.

Output is a count of 20-litre cans, rounded up, with a 10% buffer.
"""

import math

CUP_LITRES = 0.24
MINUTES_PER_CUP = 17.5   # midpoint of NIOSH's 15-20 minutes
MAX_CUPS_PER_HOUR = 6
CAN_LITRES = 20
BUFFER = 0.10


def cups_for_hour(work_minutes: int) -> int:
    return min(MAX_CUPS_PER_HOUR, math.floor(work_minutes / MINUTES_PER_CUP + 0.5))


def water_plan(work_minutes_by_hour: list[int], headcount: int) -> dict:
    if headcount < 0:
        raise ValueError("headcount must be >= 0")
    cups = sum(cups_for_hour(m) for m in work_minutes_by_hour)
    litres = round(headcount * cups * CUP_LITRES, 1)
    cans = math.ceil(round(litres * (1 + BUFFER), 6) / CAN_LITRES)
    return {"headcount": headcount, "cups_per_worker": cups, "litres": litres, "cans_20l": cans}
