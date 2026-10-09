"""A deterministic ToolBox for agent tests: a hot humid Chennai-like forecast."""

from datetime import datetime, timedelta

from agent.tools import ToolBox
from heatcore.daily import Crew, ForecastMeta
from heatcore.heat import heat_to_json
from heatcore.plan import HourHeat

NOW = datetime(2026, 10, 10, 19, 0)
SITE = {"site_id": "s1", "name": "Ramesh site", "city": "chennai"}
PROFILE = [26] * 7 + [27, 28, 29, 30, 31.5, 32.5, 32.5, 31.5, 30, 29, 28] + [27] * 6


def heat_doc() -> dict:
    start = datetime(2026, 10, 10)
    hours = [HourHeat(start + timedelta(days=d, hours=h), v + d * 0.3, v - 3)
             for d in range(4) for h, v in enumerate(PROFILE)]
    return {"run_id": "20261010T0630Z", "model": "Open-Meteo best_match",
            "issued_at": "2026-10-10T06:30:00+00:00", "hours": heat_to_json(hours)}


def toolbox(crew: Crew | None = None) -> ToolBox:
    return ToolBox(SITE, heat_doc(), crew or Crew(40, 10, 3, 1),
                   ForecastMeta("Open-Meteo best_match", datetime(2026, 10, 10, 12, 0)), NOW)
