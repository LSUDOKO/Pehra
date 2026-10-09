"""Forecast uncertainty margin (weekend version: single deterministic forecast).

No ensemble is used, so plans must never state probabilities.
"""

from datetime import datetime, timedelta

BASE_MARGIN_C = 1.0
STALE_EXTRA_C = 0.5
STALE_AFTER = timedelta(hours=18)


def is_stale(issued_at: datetime, now: datetime) -> bool:
    return now - issued_at > STALE_AFTER


def planning_margin(issued_at: datetime, now: datetime) -> tuple[float, bool]:
    """Return (margin_c, stale)."""
    stale = is_stale(issued_at, now)
    return (BASE_MARGIN_C + STALE_EXTRA_C if stale else BASE_MARGIN_C), stale
