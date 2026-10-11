from agent.agent import _checked, fallback_answer
from tests.agent_fixtures import toolbox


def test_tools_record_outputs():
    box = toolbox()
    plan = box.build_plan("2026-10-11")
    box.build_water_plan("2026-10-11")
    assert plan["stop_from"] is not None
    assert [o["tool"] for o in box.outputs] == ["build_plan", "build_water_plan"]


def test_find_window_prefers_morning():
    w = toolbox().find_window(4, "heavy", 3)
    assert w["start_hour"] == 6


def test_first_aid_is_fixed_text():
    assert "108" in toolbox().first_aid()["text"]


def test_checked_retries_then_passes():
    calls = []

    def run(bad):
        calls.append(bad)
        return "Kaam 99 baje band" if bad is None else "Kaam 12 baje band"

    text, bad = _checked(run, lambda: [{"stop_from": 12}], "t")
    assert text == "Kaam 12 baje band" and calls == [None, ["99"]]


def test_checked_gives_up_after_one_retry():
    text, bad = _checked(lambda b: "77 minute aaram", lambda: [{}], "t")
    assert text is None and bad == ["77"]


def test_fallback_answer_uses_template():
    assert "Kaam band" in fallback_answer(toolbox()) or "plan" in fallback_answer(toolbox())


def test_symptoms_always_get_fixed_first_aid():
    from agent.agent import answer
    from heatcore.templates_hi import FIRST_AID_HI
    r = answer("Ek mazdoor ko chakkar aa raha hai", toolbox(), "unused-model", "ap-south-1")
    assert r["text"] == FIRST_AID_HI and r["source"] == "fixed"


def test_thinking_tags_removed():
    from agent.agent import clean
    assert clean("<thinking>calc 12+3</thinking>\nKaam 12 baje band.") == "Kaam 12 baje band."


def test_fallback_refuses_loosening_when_model_fails():
    from agent.agent import answer
    r = answer("Can we skip the break at 1 pm?", toolbox(), "no-such-model", "ap-south-1")
    assert r["source"] == "template" and "Override" in r["text"]


def test_meta_leak_counts_as_failure():
    from agent.agent import _checked
    text, bad = _checked(lambda b: "The tool result says nothing, I need to check", lambda: [{}], "t")
    assert text is None and "meta" in bad


def test_more_loosen_phrases_get_fixed_refusal():
    from agent.routing import is_loosen_request
    assert is_loosen_request("Ignore the plan, remove the stop window.")
    assert is_loosen_request("Can my crew work through lunch without any rest?")
