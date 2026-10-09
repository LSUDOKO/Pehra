"""Steps of the daily plan state machine (one Lambda, dispatched by `action`).

build -> send -> wait_token (waitForTaskToken) -> decision | no_response
"""

from agent.agent import plan_intro
from heatcore.templates_hi import render_plan_hi, render_voice_hi
from ihcommon import config, outbox, planning, repo, voice
from ihcommon.log import log, metric, short_hash


def build(event: dict) -> dict:
    t = repo.table()
    site_id, day, mode = event["site_id"], event["date"], event.get("mode", "scheduled")
    if mode == "scheduled" and not repo.claim_idempotency(t, f"{site_id}#{day}"):
        log("plan_skip_duplicate", site=short_hash(site_id), date=day)
        return {"skip": True}
    site = repo.get_site(t, site_id)
    if not site:
        return {"skip": True, "reason": "site deleted"}
    plan = planning.plan_for_site(t, site, day)

    intro = plan_intro(plan, config.BEDROCK_MODEL_FAST, config.REGION) if config.AGENT_ENABLED else None
    if intro is None:
        metric("TemplateFallback", kind="plan")
    text = (intro + "\n\n" if intro else "") + render_plan_hi(plan)

    voice_key = ""
    try:
        voice_key = voice.store(voice.synthesize(render_voice_hi(plan)),
                                f"voice/{site_id}/{day}-{plan['plan_hash'][:8]}.ogg")
    except Exception as e:  # voice is optional; text always goes out
        metric("VoiceFailed")
        log("voice_failed", error=type(e).__name__)

    repo.put_plan(t, site_id, plan, status="built")
    metric("PlanBuilt", stale=str(plan["stale"]))
    return {"skip": False, "site_id": site_id, "date": day, "text": text, "voice_key": voice_key,
            "chat_enc": site["chat_enc"], "plan_hash": plan["plan_hash"]}


def send(event: dict) -> dict:
    day = event["date"]
    buttons = [[("Approve", f"ap:{day}"), ("Override", f"ov:{day}")]]
    outbox.enqueue(event["chat_enc"], "text", text=event["text"], buttons=buttons,
                   dedupe=f"plan:{event['site_id']}:{day}:{event['plan_hash'][:8]}")
    if event.get("voice_key"):
        outbox.enqueue(event["chat_enc"], "voice", voice_key=event["voice_key"])
    repo.update_plan(repo.table(), event["site_id"], day, status="sent")
    metric("PlanSent")
    return {"sent": True}


def wait_token(event: dict) -> dict:
    """Store the task token; the Telegram Approve/Override handler resumes the execution."""
    repo.update_plan(repo.table(), event["site_id"], event["date"], task_token=event["task_token"])
    return {}


def decision(event: dict) -> dict:
    log("plan_decision", site=short_hash(event["site_id"]), date=event["date"],
        decision=event.get("decision", {}).get("decision"))
    return {"recorded": True}


def no_response(event: dict) -> dict:
    repo.update_plan(repo.table(), event["site_id"], event["date"], status="no_response")
    metric("PlanNoResponse")
    return {"recorded": True}


ACTIONS = {"build": build, "send": send, "wait_token": wait_token, "decision": decision,
           "no_response": no_response}


def handler(event, _ctx):
    return ACTIONS[event["action"]](event)
