"""Agent tools: thin, deterministic wrappers over heatcore.

Each tool is scoped to the supervisor's own site (no site_id argument, so the model
cannot read another site). Every output is recorded for the number check.
"""

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from agent.guidance import search_guidance
from agent.roster import parse_crew_roster
from heatcore.daily import Crew, ForecastMeta, build_daily_plan
from heatcore.heat import for_date, heat_from_json
from heatcore.margin import planning_margin
from heatcore.niosh import limits
from heatcore.reschedule import find_window
from heatcore.templates_hi import FIRST_AID_HI
from heatcore.water import CAN_LITRES
from heatcore.workload import Workload

AUDIT_SUMMARY = Path(__file__).parent / "data" / "audit_summary.json"


@dataclass
class ToolBox:
    site: dict
    heat_doc: dict          # cached forecast run for the site's city
    crew: Crew
    forecast: ForecastMeta
    now: object             # datetime, IST naive
    outputs: list = field(default_factory=list)

    def _rec(self, name: str, out):
        self.outputs.append({"tool": name, "output": out})
        return out

    def _heat(self, day: str):
        h = for_date(heat_from_json(self.heat_doc["hours"]), day)
        if not h:
            raise ValueError(f"no forecast for {day}; available run {self.heat_doc['run_id']}")
        return h

    def _plan(self, day: str) -> dict:
        return build_daily_plan(self._heat(day), self.crew, self.forecast, self.now,
                                site_id=self.site["site_id"], site_name=self.site["name"])

    # ---- tools ------------------------------------------------------------
    def get_site_forecast(self, day: str) -> dict:
        _, stale = planning_margin(self.forecast.issued_at, self.now)
        hours = [{"hour": h.time_local.hour, "wbgt_sun": h.wbgt_sun, "wbgt_shade": h.wbgt_shade}
                 for h in self._heat(day)]
        return self._rec("get_site_forecast", {"date": day, "hours": hours, "stale": stale,
                         "forecast_model": self.forecast.model,
                         "forecast_issued": self.forecast.issued_at.isoformat()})

    def get_limits(self, workload: str) -> dict:
        return self._rec("get_limits", limits(Workload(workload)))

    def build_plan(self, day: str) -> dict:
        p = self._plan(day)
        keep = ("date", "stop_from", "stop_to", "heavy_stop", "rest_summary", "peak_wbgt",
                "forecast_model", "forecast_issued", "stale", "margin_c")
        out = {k: p[k] for k in keep}
        out["stop_window"] = (f"{p['stop_from']}:00 to {p['stop_to']}:00" if p["stop_from"] is not None
                              else "no stop-work window")
        hs = p.get("heavy_stop")
        out["heavy_work_stop_window"] = (f"{hs['from']}:00 to {hs['to']}:00" if hs and hs["from"] is not None
                                         else "no separate heavy-work stop window")
        return self._rec("build_plan", out)

    def build_water_plan(self, day: str) -> dict:
        return self._rec("build_water_plan", {**self._plan(day)["water"], "can_litres": CAN_LITRES})

    def build_acclimatisation_plan(self, day: str) -> dict:
        nw = self._plan(day)["new_workers"]
        return self._rec("build_acclimatisation_plan", nw or {"count": 0})

    def find_window(self, duration_hours: int, workload: str = "heavy", days_ahead: int = 3) -> dict:
        start = self.now.date()
        wanted = {date.fromordinal(start.toordinal() + i).isoformat() for i in range(1, days_ahead + 1)}
        heat = [h for h in heat_from_json(self.heat_doc["hours"])
                if h.time_local.date().isoformat() in wanted]
        margin, _ = planning_margin(self.forecast.issued_at, self.now)
        return self._rec("find_window", find_window(heat, duration_hours, workload, margin_c=margin))

    def audit_lookup(self, district: str) -> dict:
        if not AUDIT_SUMMARY.exists():
            return self._rec("audit_lookup", {"available": False})
        rows = json.loads(AUDIT_SUMMARY.read_text())["districts"]
        hit = next((r for r in rows if r["city"].lower() == district.strip().lower()), None)
        return self._rec("audit_lookup", hit or {"available": False, "district": district})

    def search_guidance(self, query: str) -> list:
        return self._rec("search_guidance", search_guidance(query))

    def parse_crew_roster(self, transcript: str) -> dict:
        return self._rec("parse_crew_roster", parse_crew_roster(transcript))

    def first_aid(self) -> dict:
        return self._rec("first_aid", {"text": FIRST_AID_HI})
