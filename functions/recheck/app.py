"""10:30 IST re-check: rebuild today's plan from the newest forecast; alert only if stricter.

For the demo, `simulate_delta_c` adds degrees to the forecast. Every such alert is
labelled SIMULATED in the message and in the record.
"""

from dataclasses import replace

from heatcore.guard import stricter_hours
from heatcore.heat import heat_to_json
from heatcore.templates_hi import render_recheck_alert_hi
from ihcommon import heatstore, outbox, planning, repo
from ihcommon.log import log, metric, short_hash


def simulated(doc: dict, delta: float) -> dict:
    hours = heatstore.hours(doc)
    bumped = [replace(h, wbgt_sun=round(h.wbgt_sun + delta, 1), wbgt_shade=round(h.wbgt_shade + delta, 1))
              for h in hours]
    return {**doc, "hours": heat_to_json(bumped), "model": f"{doc['model']} (SIMULATED +{delta:.1f} C)"}


def recheck_site(t, site: dict, day: str, now, delta: float = 0.0) -> dict:
    current = repo.get_plan(t, site["site_id"], day)
    if not current:
        return {"site": short_hash(site["site_id"]), "result": "no_plan"}
    doc = heatstore.get_latest(site["city"])
    if delta:
        doc = simulated(doc, delta)
    new = planning.plan_for_site(t, site, day, heat_doc=doc, now=now)
    worse = stricter_hours(current["plan"], new, from_hour=now.hour)
    if not worse:
        return {"site": short_hash(site["site_id"]), "result": "unchanged"}
    sk = repo.put_alert(t, site["site_id"], day, "recheck", hours=worse, simulated=bool(delta),
                        new_plan_hash=new["plan_hash"], old_plan_hash=current["plan"]["plan_hash"])
    repo.put_plan(t, site["site_id"], new, status="rechecked")
    text = render_recheck_alert_hi(new, worse)
    if delta:
        text = "[SIMULATED forecast for demo]\n" + text
    outbox.enqueue(site["chat_enc"], "text", text=text, buttons=[[("Samajh gaya", f"ack:{sk}")]])
    metric("RecheckAlert", simulated=str(bool(delta)))
    return {"site": short_hash(site["site_id"]), "result": "alerted", "hours": worse}


def handler(event, _ctx):
    event = event or {}
    t, now, day = repo.table(), planning.now_ist(), planning.today_ist()
    delta = float(event.get("simulate_delta_c", 0))
    sites = ([repo.get_site(t, event["site_id"])] if event.get("site_id") else repo.list_sites(t))
    out = []
    for site in filter(None, sites):
        try:
            out.append(recheck_site(t, site, day, now, delta))
        except Exception as e:
            log("recheck_failed", site=short_hash(site["site_id"]), error=str(e)[:200])
    log("recheck_done", results=out)
    return {"results": out}
