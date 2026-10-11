"""Tools for the personal / family assistant.

Bound to one household; no tool returns another person's data.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime

from agent.guidance import search_guidance
from heatcore.heat import for_date, heat_from_json
from heatcore.personal import Household, personal_forecast
from heatcore.templates_hi import FIRST_AID_HI


@dataclass
class PersonalToolBox:
    place: str
    household: Household
    heat_doc: dict
    margin_c: float
    conditions: dict
    now: datetime
    outputs: list = field(default_factory=list)

    def _rec(self, name: str, out):
        self.outputs.append({"tool": name, "output": out})
        return out

    def get_family_forecast(self, day: str) -> dict:
        heat = for_date(heat_from_json(self.heat_doc["hours"]), day)
        if not heat:
            raise ValueError(f"no forecast for {day}")
        f = personal_forecast(heat, self.household, margin_c=self.margin_c)
        slim = {"date": f["date"], "overall_level": f["overall_level"], "better_windows": f["better_windows"],
                "peak_wbgt_sun": f["peak_wbgt_sun"],
                "groups": {g: {"peak_level": v["peak_level"], "avoid": v["avoid"], "limit_c": v["limit_c"]}
                           for g, v in f["groups"].items()},
                "household": asdict(self.household),
                "forecast_model": self.heat_doc["model"], "forecast_issued": self.heat_doc["issued_at"]}
        return self._rec("get_family_forecast", slim)

    def get_conditions(self) -> dict:
        return self._rec("get_conditions", self.conditions)

    def search_guidance(self, query: str) -> list:
        return self._rec("search_guidance", search_guidance(query))

    def first_aid(self) -> dict:
        return self._rec("first_aid", {"text": FIRST_AID_HI})
