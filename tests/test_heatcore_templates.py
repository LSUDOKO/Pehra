import json
import re
from pathlib import Path

from heatcore.templates_hi import (
    FIRST_AID_HI,
    clock,
    render_plan_en,
    render_plan_hi,
    render_voice_hi,
)

REPLAY = Path(__file__).parents[1] / "docs/results/kharghar_replay.json"
PLAN = json.loads(REPLAY.read_text())["plan"]


def plan_numbers(plan: dict) -> set[str]:
    nums = set(re.findall(r"\d+(?:\.\d+)?", json.dumps(plan)))
    return nums | {clock(h) for h in range(24)}


def test_hindi_plan_mentions_stop_and_water():
    text = render_plan_hi(PLAN)
    assert "Kaam band" in text and f"{PLAN['water']['cans_20l']} bade can" in text
    assert "Forecast:" in text


def test_every_number_in_templates_comes_from_plan():
    allowed = plan_numbers(PLAN) | {"20"}
    for text in (render_plan_hi(PLAN), render_plan_en(PLAN), render_voice_hi(PLAN)):
        for n in re.findall(r"\d+(?:\.\d+)?", text):
            assert n in allowed, (n, text)


def test_never_says_safe():
    for text in (render_plan_hi(PLAN), render_plan_en(PLAN), render_voice_hi(PLAN)):
        assert "safe" not in text.lower()


def test_first_aid_is_fixed_and_mentions_108():
    assert "108" in FIRST_AID_HI and "jaanch nahi" in FIRST_AID_HI


def test_day_word_today_vs_tomorrow():
    from heatcore.templates_hi import day_word
    assert day_word({"date": "2026-10-11", "generated_at": "2026-10-10T19:00:00"}) == "Kal"
    assert day_word({"date": "2026-10-11", "generated_at": "2026-10-11T10:30:00"}) == "Aaj"


def test_type_and_extra_lines_render():
    plan = dict(PLAN, site_type="school", extra_lines=["- Bhaari baarish (80 mm): khudai band."])
    text = render_plan_hi(plan)
    assert "School:" in text and "Bhaari baarish" in text
