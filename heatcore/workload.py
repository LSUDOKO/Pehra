"""Workload classes mapped to NIOSH 2016 reference metabolic rates (watts).

Planning values, not measurements. Source: NIOSH Criteria for a Recommended
Standard, Occupational Exposure to Heat and Hot Environments (2016-106).
"""

from enum import StrEnum


class Workload(StrEnum):
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"


METABOLIC_RATE_W: dict[Workload, int] = {
    Workload.LIGHT: 180,
    Workload.MODERATE: 300,
    Workload.HEAVY: 415,
}

HINDI_LABEL: dict[Workload, str] = {
    Workload.LIGHT: "halka kaam",
    Workload.MODERATE: "madhyam kaam",
    Workload.HEAVY: "bhaari kaam",
}


def metabolic_rate(workload: Workload | str) -> int:
    return METABOLIC_RATE_W[Workload(workload)]
