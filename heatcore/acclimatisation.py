"""NIOSH acclimatisation schedules for new and returning workers.

Applied to exposure time (work minutes in hot hours). New workers use RAL,
not REL, until day 5. We store only counts and day numbers, never names.
"""

NEW_WORKER_FRACTIONS = (0.2, 0.4, 0.6, 0.8, 1.0)       # day 1..5
RETURNING_WORKER_FRACTIONS = (0.5, 0.6, 0.8, 1.0)      # day 1..4


def new_worker_fraction(day: int) -> float:
    _check(day)
    return NEW_WORKER_FRACTIONS[min(day, len(NEW_WORKER_FRACTIONS)) - 1]
