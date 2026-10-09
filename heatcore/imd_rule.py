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


def district_flags(
    cells_tmax: list[list[float]],
    cells_normal: list[list[float]],
    region: str = "plains",
    min_cells: int = 2,
) -> list[bool]:
    """Per-day heatwave flags for one district.

    cells_tmax[c][d] is daily max temperature for cell c on day d.
    A day qualifies if >= min_cells cells meet the rule; a heatwave is declared
    only on qualifying days that are part of a run of >= 2 consecutive days.
    """
    if not cells_tmax:
        return []
    n_days = len(cells_tmax[0])
    need = min(min_cells, len(cells_tmax))
    qual = []
    for d in range(n_days):
        hits = sum(day_level(t[d], n[d], region) != Level.NONE
                   for t, n in zip(cells_tmax, cells_normal, strict=True))
        qual.append(hits >= need)
    return [q and ((d > 0 and qual[d - 1]) or (d + 1 < n_days and qual[d + 1]))
            for d, q in enumerate(qual)]
