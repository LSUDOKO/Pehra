"""Public HTTP API (no login): worker QR page, picture poster, check-in API, static pages.

GET  /s/{token}      worker page          POST /api/checkin   break/symptom event
GET  /p/{token}      printable poster     GET  /audit, /model-card
Security: unguessable site token, per-device and per-IP rate limits, Cedar check, no names.
"""

import json
from datetime import datetime, timedelta

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
