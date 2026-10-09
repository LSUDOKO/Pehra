"""NIOSH recommended exposure limits (public-domain formulas, NIOSH 2016).

REL applies to acclimatised workers, RAL to unacclimatised workers.
Both return a WBGT limit in degrees Celsius for metabolic rate M in watts.
"""

import math

from heatcore.workload import Workload, metabolic_rate


def rel(m_watts: float) -> float:
    """Recommended Exposure Limit (acclimatised): 56.7 - 11.5 * log10(M)."""
    _check(m_watts)
    return 56.7 - 11.5 * math.log10(m_watts)


def ral(m_watts: float) -> float:
    """Recommended Alert Limit (unacclimatised): 59.9 - 14.1 * log10(M)."""
    _check(m_watts)
    return 59.9 - 14.1 * math.log10(m_watts)


def limits(workload: Workload | str) -> dict[str, float]:
    m = metabolic_rate(workload)
    return {"workload": str(Workload(workload)), "metabolic_rate_w": m,
            "rel_c": round(rel(m), 1), "ral_c": round(ral(m), 1)}


def _check(m_watts: float) -> None:
    if m_watts <= 0:
        raise ValueError(f"metabolic rate must be positive, got {m_watts}")
