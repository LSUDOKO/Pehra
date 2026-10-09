"""NIOSH acclimatisation schedules for new and returning workers.

Applied to exposure time (work minutes in hot hours). New workers use RAL,
not REL, until day 5. We store only counts and day numbers, never names.
"""

NEW_WORKER_FRACTIONS = (0.2, 0.4, 0.6, 0.8, 1.0)       # day 1..5
RETURNING_WORKER_FRACTIONS = (0.5, 0.6, 0.8, 1.0)      # day 1..4


def new_worker_fraction(day: int) -> float:
    _check(day)
    return NEW_WORKER_FRACTIONS[min(day, len(NEW_WORKER_FRACTIONS)) - 1]


def returning_worker_fraction(day: int) -> float:
    _check(day)
    return RETURNING_WORKER_FRACTIONS[min(day, len(RETURNING_WORKER_FRACTIONS)) - 1]


def uses_ral(day: int) -> bool:
    """New workers are planned against RAL until day 5."""
    return day < 5


def reduced_work_minutes(base_work_minutes: list[int], fraction: float) -> list[int]:
    """Scale each hour's work minutes down; never up (fraction capped at 1)."""
    f = min(max(fraction, 0.0), 1.0)
    return [int(m * f) for m in base_work_minutes]


def _check(day: int) -> None:
    if day < 1:
        raise ValueError(f"day must be >= 1, got {day}")
