"""IoT-style site sensors (ESP32 + DHT22 + HC-SR04, real or simulated in Wokwi / the web simulator).

A device posts readings with its own token. Readings turn into:
- weather: site-corrected WBGT vs forecast -> alert when the site is >= 1 C hotter
- tank: % full -> alert below 20% (with today's water-can order for sites)
- drain: water depth -> waterlogging alert at >= 30 cm (and a phone call if the site opted in)
Alerts are rate-limited per device so a sensor cannot spam the supervisor.
"""

import time
from datetime import UTC, datetime

from heatcore.heat import IST
from heatcore.sensor import DRAIN_HIGH_CM, TANK_LOW_PCT, compare, drain_level_cm, site_wbgt, tank_percent
from heatcore.templates_people import drain_high_text, sensor_hotter_text, tank_low_text
from ihcommon import crypto, locdata, outbox, repo

KINDS = ("weather", "tank", "drain")
ALERT_GAP_S = {"weather": 3 * 3600, "tank": 6 * 3600, "drain": 3600}
READING_TTL_DAYS = 7


def register(t, owner_kind: str, owner_id: str, kind: str, lat: float, lon: float, chat_enc: str,
             height_cm: float, key: str) -> str:
    """Create a device; returns the plaintext token (shown once to the owner)."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    token = "dev_" + crypto.new_site_token()
    th = crypto.keyed_hash(token, key)
    t.put_item(Item=repo._num({"PK": f"DEVICE#{th}", "SK": "META", "kind": kind, "owner_kind": owner_kind,
                               "owner_id": owner_id, "lat": lat, "lon": lon, "chat_enc": chat_enc,
                               "height_cm": height_cm, "token_tail": token[-4:],
                               "created": int(time.time())}))
    t.put_item(Item={"PK": f"{owner_kind.upper()}#{owner_id}", "SK": f"DEVICE#{th}", "kind": kind})
    return token


def get_device(t, token: str, key: str) -> tuple[str, dict | None]:
    th = crypto.keyed_hash(token, key)
    it = t.get_item(Key={"PK": f"DEVICE#{th}", "SK": "META"}).get("Item")
    return th, (repo._clean(it) if it else None)


def _due(dev: dict, now: float) -> bool:
    return now - float(dev.get("last_alert", 0)) >= ALERT_GAP_S[dev["kind"]]


def _forecast_hour(lat: float, lon: float, now_utc: datetime) -> tuple[dict | None, float | None]:
    doc = locdata.get_doc(lat, lon, now_utc)
    hour = now_utc.astimezone(IST).replace(tzinfo=None, minute=0, second=0, microsecond=0).isoformat()
    wx = next((w for w in doc.get("wx", []) if w["t"] == hour), None)
    fc = next((h["sun"] for h in doc.get("hours", []) if h["t"] == hour), None)
    return wx, fc


def process(t, th: str, dev: dict, reading: dict, now_utc: datetime | None = None) -> dict:
    """Store a reading, evaluate it, queue an alert if needed. Returns what the device should show."""
    now_utc = now_utc or datetime.now(UTC)
    now = now_utc.timestamp()
    out: dict = {"kind": dev["kind"], "alert": False}
    alert_text = None
    if dev["kind"] == "weather":
        temp, rh = float(reading["temp_c"]), float(reading["rh"])
        wx, fc = _forecast_hour(dev["lat"], dev["lon"], now_utc)
        w = site_wbgt(now_utc, dev["lat"], dev["lon"], temp, rh, wx or {})
        out.update({"temp_c": temp, "rh": rh, "site_wbgt_sun": w["wbgt_sun"], "site_wbgt_shade": w["wbgt_shade"],
                    "forecast_wbgt_sun": fc})
        if fc is not None:
            cmp = compare(w["wbgt_sun"], fc)
            out["diff_c"] = cmp["diff_c"]
            if cmp["hotter"]:
                out["alert"] = True
                alert_text = sensor_hotter_text(cmp)
    elif dev["kind"] == "tank":
        pct = tank_percent(float(reading["distance_cm"]), float(dev["height_cm"]))
        out["tank_pct"] = pct
        if pct < TANK_LOW_PCT:
            out["alert"] = True
            alert_text = tank_low_text(pct, _cans_today(t, dev))
    else:
        level = drain_level_cm(float(reading["distance_cm"]), float(dev["height_cm"]))
        out["water_cm"] = level
        if level >= DRAIN_HIGH_CM:
            out["alert"] = True
            alert_text = drain_high_text(level)

    t.put_item(Item=repo._num({"PK": f"DEVICE#{th}", "SK": f"R#{now_utc.isoformat(timespec='seconds')}",
                               **{k: v for k, v in out.items() if v is not None},
                               "ttl": repo.ttl_in(READING_TTL_DAYS)}))
    updates = {"latest": {k: v for k, v in out.items() if v is not None}, "last_seen": int(now)}
    if out["alert"] and alert_text and _due(dev, now):
        outbox.enqueue(dev["chat_enc"], "text", text=alert_text)
        if dev["kind"] == "drain" and dev["owner_kind"] == "site":
            site = repo.get_site(t, dev["owner_id"])
            if site:
                outbox.enqueue_call(site, alert_text.replace("🌊 ", ""))
        updates["last_alert"] = int(now)
        out["notified"] = True
    t.update_item(Key={"PK": f"DEVICE#{th}", "SK": "META"},
                  UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in updates),
                  ExpressionAttributeNames={f"#{k}": k for k in updates},
                  ExpressionAttributeValues=repo._num({f":{k}": v for k, v in updates.items()}))
    return out


def _cans_today(t, dev: dict) -> int | None:
    if dev["owner_kind"] != "site":
        return None
    from ihcommon import planning
    p = repo.get_plan(t, dev["owner_id"], planning.today_ist())
    return p["plan"]["water"]["cans_20l"] if p else None
