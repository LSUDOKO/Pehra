"""Async assistant: answers questions with the Strands agent and parses voice crew rosters.

Invoked by the webhook with InvocationType=Event, so slow model or Transcribe calls never
block Telegram. Replies go out through the SQS outbox.
"""

from agent.agent import answer
from agent.roster import parse_crew_roster, readback
from agent.tools import ToolBox
from ihcommon import channels, config, heatstore, outbox, people, planning, repo, texts
from ihcommon.crypto import decrypt
from ihcommon.log import log, metric
from ihcommon.transcribe import transcribe_ogg

MIN_VOICE_CONFIDENCE = 0.6


def toolbox_for(t, site: dict) -> ToolBox:
    doc = heatstore.get_latest(site["city"])
    return ToolBox(site, doc, planning.crew_for(t, site["site_id"]), planning.forecast_meta(doc),
                   planning.now_ist())


def on_question(t, site: dict, text: str, chat_enc: str) -> None:
    box = toolbox_for(t, site)
    r = answer(text, box, config.BEDROCK_MODEL_QA, config.REGION)
    metric("QuestionAnswered", source=r["source"])
    outbox.enqueue(chat_enc, "text", text=r["text"])


def on_voice(t, site: dict, event: dict) -> None:
    chat_id = decrypt(event["chat_enc"], config.param("data-key"))
    audio = channels.client_for(chat_id).download_file(event["file_id"])
    tr = transcribe_ogg(audio)
    log("voice_transcribed", confidence=tr["confidence"], chars=len(tr["text"]))
    if tr["confidence"] < MIN_VOICE_CONFIDENCE or not tr["text"]:
        outbox.enqueue(event["chat_enc"], "text", text=texts.CREW_UNSURE)
        return
    roster = parse_crew_roster(tr["text"])
    if roster["confidence"] == 1.0:
        pending = {k: roster[k] for k in ("headcount", "heavy_count", "new_count")} | {"new_day": 1}
        repo.set_chat_state(t, event["owner"], {"pending_crew": pending})
        outbox.enqueue(event["chat_enc"], "text", text=f"Maine suna: \"{tr['text']}\"\n{readback(roster)}",
                       buttons=[[("Haan, sahi", "crew_ok"), ("Nahi", "crew_no")]])
        return
    on_question(t, site, tr["text"], event["chat_enc"])


def on_personal_today(t, owner: str) -> None:
    person = repo.get_person(t, owner)
    if not person:
        return
    r = people.today(person)
    outbox.enqueue(person["chat_enc"], "text", text=r["text"])
    metric("PersonalForecastSent", source="on_demand")


def handler(event, _ctx):
    t = repo.table()
    if event.get("kind") == "personal_today":
        on_personal_today(t, event["owner"])
        return {"done": True}
    site = repo.get_site(t, event["site_id"])
    if not site:
        return {"skipped": True}
    if event["kind"] == "voice":
        on_voice(t, site, event)
    else:
        on_question(t, site, event["text"], event["chat_enc"])
    return {"done": True}
