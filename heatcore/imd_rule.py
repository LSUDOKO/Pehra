"""IMD heatwave rule, recreated in code for the audit.

This is NOT IMD's official declaration record. IMD's "at 2 or more stations"
condition is approximated as ">= 2 grid cells in the district" (min_cells).
"""

from enum import StrEnum

REGION_THRESHOLD_C = {"plains": 40.0, "coastal": 37.0, "hills": 30.0}


class Level(StrEnum):
    NONE = "none"
    HEATWAVE = "heatwave"
    SEVERE = "severe"


def day_level(tmax_c: float, normal_c: float, region: str = "plains") -> Level:
    """Single-cell, single-day classification before persistence."""
    if tmax_c < REGION_THRESHOLD_C[region]:
        return Level.NONE
    departure = round(tmax_c - normal_c, 2)
    if departure > 6.4 or tmax_c >= 47.0:
        return Level.SEVERE
    if departure >= 4.5 or tmax_c >= 45.0:
        return Level.HEATWAVE
    return Level.NONE
