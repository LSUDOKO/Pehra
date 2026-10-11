"""Pehra Site Box backend.

- AWS IoT Core: an IoT topic rule forwards `pehra/box/{thing}/telemetry` here; the resulting state is
  published back to `pehra/box/{thing}/cmd` (OLED lines, risk colour, siren, fan and pump relays).
- HTTPS fallback: POST /api/box {"token": "dev_...", ...} returns the same state JSON.
- 3D twin: GET /api/box/{view_token}/state (read-only) and GET /twin/{view_token} (the page).
"""

import functools
import html
import json
from pathlib import Path

import boto3

from ihcommon import authz, boxes, config, crypto, repo
from ihcommon.log import log, metric

WEB = Path(boxes.__file__).parent / "web"
if not WEB.exists():
    WEB = Path(__file__).parents[2] / "web"
TELEMETRY_KEYS = ("temp_c", "rh", "globe_c", "light_raw", "tank_distance_cm", "drain_distance_cm", "sos", "fw")


def resp(code: int, body, ctype: str = "application/json") -> dict:
    return {"statusCode": code, "headers": {"content-type": ctype, "cache-control": "no-store",
                                            "access-control-allow-origin": "*"},
            "body": body if isinstance(body, str) else json.dumps(body)}


@functools.cache
def _iot_data():
    ep = boto3.client("iot", region_name=config.REGION).describe_endpoint(endpointType="iot:Data-ATS")["endpointAddress"]
    return boto3.client("iot-data", region_name=config.REGION, endpoint_url=f"https://{ep}")


def clean(telemetry: dict) -> dict:
    out = {k: telemetry[k] for k in TELEMETRY_KEYS if k in telemetry and telemetry[k] is not None}
    if "temp_c" not in out or "rh" not in out:
        raise ValueError("temp_c and rh are required")
    return out


def authorized(box_id: str, owner: str) -> bool:
    ents = [authz.entity("Device", box_id, owner=owner), authz.entity("SensorStream", owner, owner=owner)]
    return authz.authorize(authz.uid("Device", box_id), "PostReading", authz.uid("SensorStream", owner), ents)


def on_iot(event: dict) -> dict:
    """IoT rule event: telemetry plus `box_id` = topic(3) = the authenticated thing name."""
    t = repo.table()
    box_id = event["box_id"]
    box = boxes.get_box(t, box_id)
    if not box or not authorized(box_id, f"{box['owner_kind']}:{box['owner_id']}"):
        log("iot_unknown_box", box=box_id)
        return {"ok": False}
    state = boxes.process(t, box_id, clean(event))
    _iot_data().publish(topic=f"pehra/box/{box_id}/cmd", qos=0, payload=json.dumps(state).encode())
    metric("SiteBoxCommandPublished")
    return {"ok": True, "level": state["level"]}


def on_http(event: dict) -> dict:
    config.learn_base_url(event)
    t = repo.table()
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    parts = [p for p in event.get("rawPath", "/").split("/") if p]
    key = config.param("data-key")
    if method == "POST" and parts == ["api", "box"]:
        body = json.loads(event.get("body") or "{}")
        token = str(body.get("token", ""))
        if not token.startswith("dev_") or len(token) > 64:
            return resp(400, {"error": "bad token"})
        box = boxes.box_for_token(t, token, key, "device")
        if not box:
            return resp(404, {"error": "unknown box"})
        if repo.rate_limited(t, crypto.keyed_hash(token, key), 12):
            return resp(429, {"error": "slow down"})
        if not authorized(box["box_id"], f"{box['owner_kind']}:{box['owner_id']}"):
            return resp(403, {"error": "forbidden"})
        try:
            return resp(200, boxes.process(t, box["box_id"], clean(body)))
        except (ValueError, TypeError) as e:
            return resp(400, {"error": str(e)})
    if method == "GET" and len(parts) == 4 and parts[:2] == ["api", "box"] and parts[3] == "state":
        box = boxes.box_for_token(t, parts[2], key, "view")
        if not box:
            return resp(404, {"error": "unknown box"})
        st = boxes.last_state(box)
        return resp(200, st or {"box_id": box["box_id"], "site_name": box.get("site_name", ""), "waiting": True})
    if method == "GET" and len(parts) == 2 and parts[0] == "twin":
        box = boxes.box_for_token(t, parts[1], key, "view")
        if not box or not (WEB / "twin" / "index.html").exists():
            return resp(404, "Twin not found", "text/plain")
        page = (WEB / "twin" / "index.html").read_text()
        page = page.replace("{{STATE_URL}}", f"{config.PUBLIC_BASE_URL.rstrip('/')}/api/box/{parts[1]}/state")
        page = page.replace("{{SITE_NAME}}", html.escape(box.get("site_name", "Site")))
        return resp(200, page, "text/html; charset=utf-8")
    return resp(404, {"error": "not found"})


def handler(event, _ctx):
    if "requestContext" in event:
        return on_http(event)
    return on_iot(event)
