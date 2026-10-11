"""Public HTTP API (no login): worker QR page, picture poster, check-in API, static pages.

GET  /s/{token}      worker page          POST /api/checkin   break/symptom event
GET  /p/{token}      printable poster     GET  /audit, /model-card
Security: unguessable site token, per-device and per-IP rate limits, Cedar check, no names.
"""

import html as html_lib
import json
from datetime import datetime, timedelta

import boto3

from heatcore.heat import IST
from heatcore.templates_hi import CALL_SYMPTOM_HI, FIRST_AID_HI, render_symptom_alert_hi
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
            outbox.enqueue_call(site, CALL_SYMPTOM_HI)  # only if the supervisor opted in
            metric("SymptomReported")
        return resp(200, {"ok": True, "first_aid": FIRST_AID_HI})
    repo.put_checkin(t, site["site_id"], day, kind, dev_hash)
    metric("BreakLogged", type=kind)
    log("checkin", site=short_hash(site["site_id"]), type=kind)
    return resp(200, {"ok": True})


def _ts(item: dict) -> datetime:
    # SK = CHK#{date}#{iso-with-offset}#{dev6}
    return datetime.fromisoformat(item["SK"].split("#")[2]).astimezone(IST).replace(tzinfo=None)


SENSOR_LIMIT_PER_MIN = 12


def sensor(t, body: dict, ip: str) -> dict:
    """POST /api/sensor from a real or simulated ESP32. The token identifies the device."""
    from ihcommon import devices

    token = str(body.get("device_token", ""))
    if not token.startswith("dev_") or len(token) > 64:
        return resp(400, {"error": "bad token"})
    key = config.param("data-key")
    th, dev = devices.get_device(t, token, key)
    if not dev:
        return resp(404, {"error": "unknown device"})
    if repo.rate_limited(t, th, SENSOR_LIMIT_PER_MIN) or \
            repo.rate_limited(t, crypto.keyed_hash(ip, key), IP_LIMIT_PER_MIN):
        return resp(429, {"error": "slow down"})
    owner = f"{dev['owner_kind']}:{dev['owner_id']}"
    if not authz.authorize(authz.uid("Device", th), "PostReading", authz.uid("SensorStream", owner),
                           [authz.entity("Device", th, owner=owner), authz.entity("SensorStream", owner, owner=owner)]):
        return resp(403, {"error": "forbidden"})
    try:
        if dev["kind"] == "weather":
            float(body["temp_c"]), float(body["rh"])
        else:
            float(body["distance_cm"])
        out = devices.process(t, th, dev, body)
    except (KeyError, TypeError, ValueError) as e:
        return resp(400, {"error": f"bad reading: {e}"})
    metric("SensorReading", kind=dev["kind"])
    return resp(200, out)


def page_device(t, token: str) -> dict:
    from ihcommon import devices

    _, dev = devices.get_device(t, token, config.param("data-key"))
    if not dev:
        return resp(404, "Device not found.", "text/plain; charset=utf-8")
    labels = {"weather": "Weather sensor · DHT22", "tank": "Water tank · HC-SR04", "drain": "Drain level · HC-SR04"}
    h = int(float(dev.get("height_cm") or 100))
    tpl = (WEB / "device" / "index.html").read_text()
    for k, v in {"KIND_LABEL": labels[dev["kind"]], "KIND": dev["kind"], "API_URL": f"{base_url()}/api/sensor",
                 "TOKEN": token, "HEIGHT": str(h), "HALF": str(h // 2)}.items():
        tpl = tpl.replace("{{" + k + "}}", html_lib.escape(v))
    return resp(200, tpl, "text/html; charset=utf-8")


IMAGE_TYPES = {".webp": "image/webp", ".png": "image/png", ".gif": "image/gif", ".jpg": "image/jpeg"}
MEDIA = {"twin.mp4", "wokwi.mp4", "pehra_brand.mp4", "box_sos.mp4"}  # large files live in the media bucket
ASSETS = {
    "home.css": "assets/home.css",
    "home.js": "assets/home.js",
    "favicon.svg": "assets/favicon.svg",
    "gsap.min.js": "vendor/gsap-3.13.0.min.js",
    "ScrollTrigger.min.js": "vendor/ScrollTrigger-3.13.0.min.js",
}
STATIC_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}


def image(name: str) -> dict:
    import base64
    import re

    path = WEB / "img" / name
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,80}", name) or path.suffix not in IMAGE_TYPES or not path.exists():
        return resp(404, "not found", "text/plain")
    return {"statusCode": 200, "isBase64Encoded": True,
            "headers": {"content-type": IMAGE_TYPES[path.suffix], "cache-control": "max-age=86400",
                        "x-content-type-options": "nosniff"},
            "body": base64.b64encode(path.read_bytes()).decode()}


def media(name: str) -> dict:
    """Videos are too big for a Lambda response: redirect to a short-lived S3 link in the media bucket."""
    if name not in MEDIA or not config.MEDIA_BUCKET:
        return resp(404, "not found", "text/plain")
    url = boto3.client("s3", region_name=config.REGION).generate_presigned_url(
        "get_object", Params={"Bucket": config.MEDIA_BUCKET, "Key": f"web/{name}"}, ExpiresIn=3600)
    return {"statusCode": 302, "headers": {"location": url, "cache-control": "max-age=600"}, "body": ""}


def static(name: str) -> dict:
    path = WEB / name
    if not path.exists():
        return resp(404, "not found", "text/plain")
    if path.suffix in STATIC_TYPES:
        return resp(200, path.read_text(), STATIC_TYPES[path.suffix], "max-age=3600")
    return html_resp(path.read_text())


def handler(event, _ctx):
    config.learn_base_url(event)
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")
    ip = event.get("requestContext", {}).get("http", {}).get("sourceIp", "")
    parts = [p for p in path.split("/") if p]
    # Public pages and allowlisted assets do not need a database connection.
    if method == "GET":
        pages = {"/": "home/index.html", "/site.css": "india.css",
                 "/audit": "audit/index.html", "/audit/": "audit/index.html",
                 "/model-card": "model_card/index.html", "/model-card/": "model_card/index.html"}
        if path in pages:
            return static(pages[path])
        if parts and parts[0] == "img":
            return image(parts[1]) if len(parts) == 2 else resp(404, "not found", "text/plain")
        if parts and parts[0] == "media":
            return media(parts[1]) if len(parts) == 2 else resp(404, "not found", "text/plain")
        if parts and parts[0] == "assets":
            if len(parts) == 2 and parts[1] in ASSETS:
                return static(ASSETS[parts[1]])
            return resp(404, "not found", "text/plain")
    t = repo.table()
    try:
        if method == "POST" and path == "/api/sensor":
            return sensor(t, json.loads(event.get("body") or "{}"), ip)
        if method == "GET" and len(parts) == 2 and parts[0] == "device":
            return page_device(t, parts[1])
        if method == "POST" and path == "/api/checkin":
            return checkin(t, json.loads(event.get("body") or "{}"), ip)
        if method == "GET" and len(parts) == 2 and parts[0] == "s":
            return page_worker(t, parts[1])
        if method == "GET" and len(parts) == 2 and parts[0] == "p":
            return page_poster(t, parts[1])
    except json.JSONDecodeError:
        return resp(400, {"error": "bad json"})
    return resp(404, {"error": "not found"})
