"""Strands agent on Bedrock with a mandatory number check and a fixed-text fallback.

The model explains and answers; heatcore tools do every calculation.
"""

import re

from agent.number_check import verify_numbers
from agent.prompts import INTRO_ACTION_REST, INTRO_ACTION_STOP, INTRO_PROMPT, SYSTEM_PROMPT
from agent.routing import LOOSEN_REPLY, is_loosen_request, is_symptom
from agent.tools import ToolBox
from heatcore.templates_hi import day_word, render_plan_hi
from ihcommon.log import log, metric

MAX_TOKENS = 400
TEMPERATURE = 0.2


THINKING_RE = re.compile(r"<thinking>.*?</thinking>\s*", re.S | re.I)


def clean(text: str) -> str:
    """Drop model reasoning tags (some Bedrock models emit <thinking>) before anything is checked or sent."""
    return THINKING_RE.sub("", str(text)).replace("<thinking>", "").strip()


def _model(model_id: str, region: str):
    from strands.models import BedrockModel
    return BedrockModel(model_id=model_id, region_name=region, temperature=TEMPERATURE,
                        max_tokens=MAX_TOKENS)


def _strands_tools(box: ToolBox) -> list:
    from strands import tool

    @tool
    def get_site_forecast(day: str) -> dict:
        """Hourly WBGT in sun and shade for this site on a date (YYYY-MM-DD).

        Includes forecast model, issue time and stale flag.
        """
        return box.get_site_forecast(day)

    @tool
    def get_limits(workload: str) -> dict:
        """NIOSH heat limits in deg C (REL acclimatised, RAL unacclimatised).

        workload is light, moderate or heavy.
        """
        return box.get_limits(workload)

    @tool
    def build_plan(day: str) -> dict:
        """The site's work-rest plan for a date (YYYY-MM-DD).

        Stop window, rest minutes per period, peak WBGT and forecast details.
        """
        return box.build_plan(day)

    @tool
    def build_water_plan(day: str) -> dict:
        """Drinking water for the crew on a date (YYYY-MM-DD) as litres and number of cans."""
        return box.build_water_plan(day)

    @tool
    def build_acclimatisation_plan(day: str) -> dict:
        """Reduced schedule for new workers on a date (YYYY-MM-DD)."""
        return box.build_acclimatisation_plan(day)

    @tool
    def find_window(duration_hours: int, workload: str = "heavy", days_ahead: int = 3) -> dict:
        """Coolest contiguous working window of duration_hours in the next days_ahead days for a task."""
        return box.find_window(duration_hours, workload, days_ahead)

    @tool
    def audit_lookup(district: str) -> dict:
        """Invisible-heat-day counts for a district from the audit (a minimum; ERA5 smooths extremes)."""
        return box.audit_lookup(district)

    @tool
    def search_guidance(query: str) -> list:
        """Short vetted heat-safety passages with sources (NIOSH, NDMA, OSHA, IMD)."""
        return box.search_guidance(query)

    @tool
    def first_aid() -> dict:
        """The fixed first-aid text for heat symptoms. Repeat it exactly; never change it."""
        return box.first_aid()

    return [get_site_forecast, get_limits, build_plan, build_water_plan, build_acclimatisation_plan,
            find_window, audit_lookup, search_guidance, first_aid]


def _checked(run, outputs_fn, kind: str) -> tuple[str | None, list[str]]:
    """Run, check numbers, retry once with the unmatched list. None means use the template."""
    text = run(None)
    bad = verify_numbers(text, outputs_fn())
    if bad:
        metric("NumberCheckFailed", kind=kind)
        log("number_check_failed", kind=kind, unmatched=bad, attempt=1)
        text = run(bad)
        bad = verify_numbers(text, outputs_fn())
        if bad:
            metric("NumberCheckFallback", kind=kind)
            log("number_check_failed", kind=kind, unmatched=bad, attempt=2)
            return None, bad
    return text, []


def answer(question: str, box: ToolBox, model_id: str, region: str) -> dict:
    """Answer a supervisor's question. Falls back to the fixed plan text on any failure."""
    if is_symptom(question):
        return {"text": box.first_aid()["text"], "source": "fixed", "tools": ["first_aid"]}
    from strands import Agent

    header = (f"Today (IST): {box.now.date().isoformat()}. Site: {box.site['name']} "
              f"({box.site['city']}). Crew: {box.crew.headcount} workers.\n\n")
    try:
        agent = Agent(model=_model(model_id, region), system_prompt=SYSTEM_PROMPT,
                      tools=_strands_tools(box), callback_handler=None)

        def run(bad):
            if bad is None:
                return clean(agent(header + question))
            return clean(agent(f"Remove or correct these numbers; they are not in any tool result: "
                             f"{', '.join(bad)}. Rewrite your last answer."))

        text, bad = _checked(run, lambda: box.outputs, "answer")
        if text:
            return {"text": text, "source": "agent", "tools": [o["tool"] for o in box.outputs]}
    except Exception as e:
        metric("AgentError", kind="answer")
        log("agent_error", kind="answer", error=type(e).__name__, detail=str(e)[:300])
    if is_loosen_request(question):
        return {"text": LOOSEN_REPLY, "source": "template", "tools": []}
    return {"text": fallback_answer(box), "source": "template", "tools": []}


def fallback_answer(box: ToolBox) -> str:
    day = box.now.date().isoformat()
    try:
        plan = box._plan(day)
    except ValueError:
        return "Maaf kijiye, abhi jawab nahi de sakta. Kripya /plan_now bhejiye."
    return "Abhi AI jawab nahi de pa raha. Aaj ka tay plan:\n\n" + render_plan_hi(plan)


def plan_intro(plan: dict, model_id: str, region: str) -> str | None:
    """One or two AI sentences above the fixed plan text; None if Bedrock fails or a number is wrong."""
    try:
        from strands import Agent
        agent = Agent(model=_model(model_id, region), callback_handler=None)
        slim = {k: plan[k] for k in ("stop_from", "stop_to", "peak_wbgt", "stale", "date")}
        has_stop = plan["stop_from"] is not None
        prompt = INTRO_PROMPT.format(
            day_word=day_word(plan).lower(),
            risk="dangerous for heavy and long work" if has_stop else "a moderate risk")

        def run(bad):
            extra = "" if bad is None else f"\nDo not use these numbers: {', '.join(bad)}."
            return clean(Agent(model=agent.model, callback_handler=None)(prompt + extra))

        text, _ = _checked(run, lambda: [slim], "intro")
        if not text or re.search(r"[\u0900-\u097F]", text):  # must be Roman script
            return None
        first = re.split(r"(?<=[.!?])\s+", text.strip())[0]
        return f"{first}\n{INTRO_ACTION_STOP if has_stop else INTRO_ACTION_REST}"
    except Exception as e:
        metric("AgentError", kind="intro")
        log("agent_error", kind="intro", error=type(e).__name__, detail=str(e)[:300])
        return None


def _personal_tools(box) -> list:
    from strands import tool

    @tool
    def get_family_forecast(day: str) -> dict:
        """Heat levels for this household on a date (YYYY-MM-DD): overall level, per-group levels,
        hours to avoid, better hours to go out, peak WBGT and forecast details."""
        return box.get_family_forecast(day)

    @tool
    def get_conditions() -> dict:
        """Today's rain category, warm-night flag and river-flood signal for this place."""
        return box.get_conditions()

    @tool
    def search_guidance(query: str) -> list:
        """Short vetted heat-safety passages with sources (NIOSH, NDMA, OSHA, IMD)."""
        return box.search_guidance(query)

    @tool
    def first_aid() -> dict:
        """The fixed first-aid text for heat symptoms. Repeat it exactly; never change it."""
        return box.first_aid()

    return [get_family_forecast, get_conditions, search_guidance, first_aid]


def answer_personal(question: str, box, model_id: str, region: str) -> dict:
    """Answer a family's question with the number check; fall back to today's fixed message."""
    from agent.prompts import PERSONAL_PROMPT

    if is_symptom(question):
        return {"text": box.first_aid()["text"], "source": "fixed", "tools": ["first_aid"]}
    hh = box.household
    header = (f"Today (IST): {box.now.date().isoformat()}. Place: {box.place}. "
              f"Household: {hh.adults} adults, {hh.elderly} elderly, {hh.young_children} young children, "
              f"{hh.pregnant} pregnant, {hh.chronic} with chronic illness, "
              f"works outdoors: {hh.works_outdoors}.\n\n")
    try:
        from strands import Agent
        agent = Agent(model=_model(model_id, region), system_prompt=PERSONAL_PROMPT,
                      tools=_personal_tools(box), callback_handler=None)

        def run(bad):
            if bad is None:
                return clean(agent(header + question))
            return clean(agent(f"Remove or correct these numbers; they are not in any tool result: "
                               f"{', '.join(bad)}. Rewrite your last answer."))

        text, _ = _checked(run, lambda: box.outputs, "personal")
        if text:
            return {"text": text, "source": "agent", "tools": [o["tool"] for o in box.outputs]}
    except Exception as e:
        metric("AgentError", kind="personal")
        log("agent_error", kind="personal", error=type(e).__name__, detail=str(e)[:300])
    return {"text": None, "source": "template", "tools": []}
