"""07:00 IST: today's personal/family heat message for every registered person, plus an opt-in
Hindi call to an elderly relative on 'bahut zyada' or 'khatarnak' days (at most once a day).

Tiles are computed once and shared by everyone in the same 0.25-degree cell.
"""

from datetime import UTC, datetime

from heatcore.heat import IST
from ihcommon import outbox, people, repo
from ihcommon.log import log, metric, short_hash


def send_one(t, person: dict, now: datetime) -> dict:
    r = people.today(person, now)
    outbox.enqueue(person["chat_enc"], "text", text=r["text"])
    called = False
    day = now.astimezone(IST).date().isoformat()
    if r["call_text"] and person.get("family_enc") and person.get("last_family_call") != day:
        outbox.enqueue(person["family_enc"], "call", text=r["call_text"])
        repo.update_person(t, person["owner_hash"], last_family_call=day)
        called = True
    return {"level": r["forecast"]["overall_level"], "family_call": called}


def handler(event, _ctx):
    t, now = repo.table(), datetime.now(UTC)
    results = []
    for person in repo.list_people(t):
        try:
            results.append(send_one(t, person, now))
        except Exception as e:
            log("personal_failed", person=short_hash(person["owner_hash"]), error=str(e)[:200])
    metric("PersonalForecastSent", len(results), source="morning")
    metric("FamilyCallQueued", sum(r["family_call"] for r in results))
    log("personal_done", people=len(results))
    return {"sent": len(results), "family_calls": sum(r["family_call"] for r in results)}
