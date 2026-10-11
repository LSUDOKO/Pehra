"""Pehra Site Box registry and processing (AWS IoT Core MQTT or HTTPS fallback).

Tokens: a device token (posts readings over HTTPS) and a view token (read-only, for the 3D twin).
Both are stored only as keyed hashes. The box id doubles as the AWS IoT thing name.
"""

import json
import time
from datetime import UTC, datetime

from heatcore.heat import IST
from heatcore.sensor import site_wbgt
from heatcore.sitebox import evaluate
from heatcore.templates_hi import CALL_SYMPTOM_HI
from heatcore.templates_people import drain_high_text, tank_low_text
from ihcommon import crypto, outbox, repo
from ihcommon.log import log, metric

ALERT_GAP_S = {"tank_low": 6 * 3600, "waterlogging": 3600, "hotter_than_forecast": 3 * 3600, "sos": 120}
SOS_WINDOW_S = 600


def register(t, owner_kind: str, owner_id: str, lat: float, lon: float, chat_enc: str, site_name: str,
             key: str, tank_height_cm: float = 120, drain_mount_cm: float = 100) -> dict:
    box_id = "box-" + crypto.new_site_token()[:8].lower().replace("_", "x").replace("-", "y")
    dev, view = "dev_" + crypto.new_site_token(), "view_" + crypto.new_site_token()
    t.put_item(Item=repo._num({"PK": f"BOX#{box_id}", "SK": "META", "owner_kind": owner_kind, "owner_id": owner_id,
                               "lat": lat, "lon": lon, "chat_enc": chat_enc, "site_name": site_name[:60],
                               "tank_height_cm": tank_height_cm, "drain_mount_cm": drain_mount_cm,
                               "pump": False, "created": int(time.time())}))
    t.put_item(Item={"PK": f"BOXDEV#{crypto.keyed_hash(dev, key)}", "SK": "META", "box_id": box_id})
    t.put_item(Item={"PK": f"BOXVIEW#{crypto.keyed_hash(view, key)}", "SK": "META", "box_id": box_id})
    return {"box_id": box_id, "device_token": dev, "view_token": view}


def get_box(t, box_id: str) -> dict | None:
    it = t.get_item(Key={"PK": f"BOX#{box_id}", "SK": "META"}).get("Item")
    return repo._clean(it) if it else None


def box_for_token(t, token: str, key: str, kind: str) -> dict | None:
    pk = ("BOXDEV#" if kind == "device" else "BOXVIEW#") + crypto.keyed_hash(token, key)
    it = t.get_item(Key={"PK": pk, "SK": "META"}).get("Item")
    box = get_box(t, it["box_id"]) if it else None
    return {**box, "box_id": it["box_id"]} if box else None


def _forecast(lat: float, lon: float, now_utc: datetime):
    from ihcommon import devices
    try:
        return devices._forecast_hour(lat, lon, now_utc)
    except Exception as e:  # forecast is optional for a box
        log("box_forecast_failed", error=type(e).__name__)
        return None, None


def _due(box: dict, kind: str, now: float) -> bool:
    return now - float((box.get("last_alerts") or {}).get(kind, 0)) >= ALERT_GAP_S[kind]


def process(t, box_id: str, telemetry: dict, now_utc: datetime | None = None) -> dict:
    """Evaluate telemetry, persist state, send rate-limited alerts. Returns the state (command) dict."""
    box = get_box(t, box_id)
    if not box:
        raise KeyError("unknown box")
    now_utc = now_utc or datetime.now(UTC)
    now = now_utc.timestamp()
    wx, fc = _forecast(box["lat"], box["lon"], now_utc)
    fallback = None
    if telemetry.get("globe_c") is None and wx:
        fallback = site_wbgt(now_utc, box["lat"], box["lon"], float(telemetry["temp_c"]), float(telemetry["rh"]), wx)["wbgt_sun"]
    sos_recent = now - float(box.get("last_sos", 0)) < SOS_WINDOW_S
    state = evaluate(telemetry, tank_height_cm=float(box["tank_height_cm"]), drain_mount_cm=float(box["drain_mount_cm"]),
                     forecast_wbgt_c=fc, fallback_wbgt_c=fallback, prev_pump=bool(box.get("pump")),
                     sos_recent=sos_recent, now=now_utc.astimezone(IST).replace(tzinfo=None),
                     box_id=box_id, site_name=box.get("site_name", ""))
    last_alerts = dict(box.get("last_alerts") or {})
    for kind in state["alerts"]:
        if kind == "sos" and not telemetry.get("sos"):
            continue  # only a fresh press notifies
        if not _due(box, kind, now):
            continue
        _notify(t, box, kind, state)
        last_alerts[kind] = int(now)
    upd = {"pump": state["pump_on"], "last_state": json.dumps(state), "last_seen": int(now), "last_alerts": last_alerts}
    if telemetry.get("sos"):
        upd["last_sos"] = int(now)
    t.update_item(Key={"PK": f"BOX#{box_id}", "SK": "META"},
                  UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in upd),
                  ExpressionAttributeNames={f"#{k}": k for k in upd},
                  ExpressionAttributeValues=repo._num({f":{k}": v for k, v in upd.items()}))
    t.put_item(Item=repo._num({"PK": f"BOX#{box_id}", "SK": f"R#{now_utc.isoformat(timespec='seconds')}",
                               "wbgt_c": state["wbgt_c"], "level": state["level"], "ttl": repo.ttl_in(7)}))
    metric("SiteBoxReading", level=state["level"])
    return state


def _notify(t, box: dict, kind: str, state: dict) -> None:
    r = state["readings"]
    site = repo.get_site(t, box["owner_id"]) if box["owner_kind"] == "site" else None
    if kind == "tank_low":
        text = tank_low_text(r["tank_pct"], None) + " Pump chalu kiya gaya."
    elif kind == "waterlogging":
        text = drain_high_text(r["drain_cm"])
    elif kind == "hotter_than_forecast":
        text = (f"🌡 Site Box: WBGT {state['wbgt_c']}°C, forecast {state['forecast_wbgt_c']}°C. "
                f"Site forecast se zyada garam hai. {state['rest_minutes']} minute aaram har ghante.")
    else:
        text = "🆘 Site Box: ek mazdoor ne SOS dabaya (chakkar / bimari). Turant jaiye. Chhaon, paani, aaram. Behoshi ho to 108."
    outbox.enqueue(box["chat_enc"], "text", text=text)
    if site and kind in ("sos", "waterlogging"):
        outbox.enqueue_call(site, CALL_SYMPTOM_HI if kind == "sos" else text.replace("🌊 ", ""))
    metric("SiteBoxAlert", kind=kind)


def last_state(box: dict) -> dict | None:
    return json.loads(box["last_state"]) if box.get("last_state") else None
