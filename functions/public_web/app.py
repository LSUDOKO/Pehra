"""Public HTTP API (no login): worker QR page, picture poster, check-in API, static pages.

GET  /s/{token}      worker page          POST /api/checkin   break/symptom event
GET  /p/{token}      printable poster     GET  /audit, /model-card
Security: unguessable site token, per-device and per-IP rate limits, Cedar check, no names.
"""

import json
from datetime import datetime, timedelta

from heatcore.heat import IST
from heatcore.templates_hi import FIRST_AID_HI, render_symptom_alert_hi
from ihcommon import authz, config, crypto, outbox, planning, repo
from ihcommon.log import log, metric, short_hash
from ihcommon.web import WEB, poster_page, worker_page

EVENT_TYPES = ("break_start", "break_end", "symptom")
DEVICE_LIMIT_PER_MIN = 10
IP_LIMIT_PER_MIN = 60
SYMPTOM_DEDUPE = timedelta(minutes=2)


def resp(status: int, body, ctype: str = "application/json", cache: str = "no-store") -> dict:
    if not isinstance(body, str):
        body = json.dumps(body)
    return {"statusCode": status, "headers": {"content-type": ctype, "cache-control": cache,
                                              "x-content-type-options": "nosniff"}, "body": body}


def html_resp(body: str) -> dict:
    return resp(200, body, "text/html; charset=utf-8", "max-age=300")


def current_plan(t, site_id: str) -> dict | None:
    p = repo.get_plan(t, site_id, planning.today_ist())
    return p["plan"] if p else None


def base_url() -> str:
    return config.PUBLIC_BASE_URL.rstrip("/")


def page_worker(t, token: str) -> dict:
    site = repo.site_for_token(t, token)
    if not site:
        return resp(404, "Yeh QR code sahi nahi hai.", "text/plain; charset=utf-8")
    return html_resp(worker_page(site, current_plan(t, site["site_id"]), f"{base_url()}/api/checkin"))


def page_poster(t, token: str) -> dict:
    site = repo.site_for_token(t, token)
    if not site:
        return resp(404, "Poster nahi mila.", "text/plain; charset=utf-8")
    plan = current_plan(t, site["site_id"])
    if not plan:
        try:
            plan = planning.plan_for_site(t, site, planning.today_ist())
        except Exception:
            return resp(404, "Aaj ka plan abhi nahi bana.", "text/plain; charset=utf-8")
    return html_resp(poster_page(site, plan, f"{base_url()}/s/{token}"))


def checkin(t, body: dict, ip: str) -> dict:
    kind, token, device = body.get("type"), body.get("site_token", ""), body.get("device_token", "")
    if kind not in EVENT_TYPES or not token or not (8 <= len(device) <= 64):
        return resp(400, {"error": "bad request"})
    key = config.param("data-key")
    dev_hash = crypto.keyed_hash(device, key)
    if repo.rate_limited(t, dev_hash, DEVICE_LIMIT_PER_MIN) or \
            repo.rate_limited(t, crypto.keyed_hash(ip, key), IP_LIMIT_PER_MIN):
        metric("CheckinRateLimited")
        return resp(429, {"error": "slow down"})
    site = repo.site_for_token(t, token)
    if not site:
        return resp(404, {"error": "unknown site"})
    worker = authz.entity("Worker", dev_hash, site=authz.uid("Site", site["site_id"]))
    if not authz.authorize(authz.uid("Worker", dev_hash), "LogCheckIn", authz.uid("Site", site["site_id"]),
                           authz.site_entities(site) + [worker]):
        return resp(403, {"error": "forbidden"})

    day, now = planning.today_ist(), planning.now_ist()
    if kind == "symptom":
        recent = [c for c in repo.day_items(t, site["site_id"], "CHK", day) if c["type"] == "symptom"]
        mine = [c for c in recent if c["device_token_hash"] == dev_hash
                and _ts(c) > now - SYMPTOM_DEDUPE]
        if not mine:
            repo.put_checkin(t, site["site_id"], day, kind, dev_hash)
            last_hour = 1 + sum(1 for c in recent if _ts(c) > now - timedelta(hours=1))
            outbox.enqueue(site["chat_enc"], "text",
                           text=render_symptom_alert_hi(now.strftime("%H:%M"), last_hour))
            metric("SymptomReported")
        return resp(200, {"ok": True, "first_aid": FIRST_AID_HI})
    repo.put_checkin(t, site["site_id"], day, kind, dev_hash)
    metric("BreakLogged", type=kind)
    log("checkin", site=short_hash(site["site_id"]), type=kind)
    return resp(200, {"ok": True})


def _ts(item: dict) -> datetime:
    # SK = CHK#{date}#{iso-with-offset}#{dev6}
    return datetime.fromisoformat(item["SK"].split("#")[2]).astimezone(IST).replace(tzinfo=None)


def static(name: str) -> dict:
    path = WEB / name
    return html_resp(path.read_text()) if path.exists() else resp(404, "not found", "text/plain")


def handler(event, _ctx):
    t = repo.table()
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")
    ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "")
    parts = [p for p in path.split("/") if p]
    try:
        if method == "POST" and path == "/api/checkin":
            return checkin(t, json.loads(event.get("body") or "{}"), ip)
        if method == "GET" and len(parts) == 2 and parts[0] == "s":
            return page_worker(t, parts[1])
        if method == "GET" and len(parts) == 2 and parts[0] == "p":
            return page_poster(t, parts[1])
        if method == "GET" and path in ("/audit", "/audit/"):
            return static("audit/index.html")
        if method == "GET" and path in ("/model-card", "/model-card/"):
            return static("model_card/index.html")
    except json.JSONDecodeError:
        return resp(400, {"error": "bad json"})
    return resp(404, {"error": "not found"})
