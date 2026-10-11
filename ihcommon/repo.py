"""DynamoDB single-table access (see invisible-heat-agent-pack/07-architecture.md).

Only headcounts and hashed/encrypted identifiers are stored; never worker names.
"""

import json
import time
from datetime import datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from ihcommon import config

DAY_S = 86400
CHECKIN_TTL_DAYS = 90


def table(name: str | None = None):
    return boto3.resource("dynamodb", region_name=config.REGION).Table(name or config.TABLE)


def _clean(item: dict) -> dict:
    """Decimals back to int/float for JSON-friendly use."""
    return json.loads(json.dumps(item, default=lambda d: float(d) if d % 1 else int(d)))


def _num(obj):
    return json.loads(json.dumps(obj), parse_float=Decimal)


def ttl_in(days: int) -> int:
    return int(time.time()) + days * DAY_S


# ---- sites -----------------------------------------------------------------

def put_site(t, site: dict, owner_hash: str, chat_enc: str) -> None:
    sid = site["site_id"]
    t.put_item(Item=_num({**site, "PK": f"SITE#{sid}", "SK": "META", "owner_hash": owner_hash,
                          "chat_enc": chat_enc, "GSI1PK": "SITES", "GSI1SK": sid}))
    t.put_item(Item={"PK": f"CHAT#{owner_hash}", "SK": "META", "site_id": sid})
    t.put_item(Item={"PK": f"TOKEN#{site['site_token']}", "SK": "META", "site_id": sid})


def get_site(t, site_id: str) -> dict | None:
    it = t.get_item(Key={"PK": f"SITE#{site_id}", "SK": "META"}).get("Item")
    return _clean(it) if it else None


def site_for_chat(t, owner_hash: str) -> dict | None:
    it = t.get_item(Key={"PK": f"CHAT#{owner_hash}", "SK": "META"}).get("Item")
    return get_site(t, it["site_id"]) if it and it.get("site_id") else None


def site_for_token(t, token: str) -> dict | None:
    it = t.get_item(Key={"PK": f"TOKEN#{token}", "SK": "META"}).get("Item")
    return get_site(t, it["site_id"]) if it else None


def list_sites(t) -> list[dict]:
    out, kw = [], {"IndexName": "GSI1", "KeyConditionExpression": Key("GSI1PK").eq("SITES")}
    while True:
        r = t.query(**kw)
        out += [_clean(i) for i in r["Items"]]
        if "LastEvaluatedKey" not in r:
            return out
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


# ---- chat state (multi-step conversations, e.g. waiting for an override reason) ----

def set_chat_state(t, owner_hash: str, state: dict | None) -> None:
    t.update_item(Key={"PK": f"CHAT#{owner_hash}", "SK": "META"},
                  UpdateExpression="SET #s = :s", ExpressionAttributeNames={"#s": "state"},
                  ExpressionAttributeValues={":s": _num(state or {})})


def get_chat_state(t, owner_hash: str) -> dict:
    it = t.get_item(Key={"PK": f"CHAT#{owner_hash}", "SK": "META"}).get("Item") or {}
    return _clean(it.get("state") or {})


# ---- crew --------------------------------------------------------------------

def put_crew(t, site_id: str, date: str, crew: dict) -> None:
    for sk in (f"CREW#{date}", "CREW#latest"):
        t.put_item(Item=_num({"PK": f"SITE#{site_id}", "SK": sk, **crew}))


def get_crew(t, site_id: str) -> dict | None:
    it = t.get_item(Key={"PK": f"SITE#{site_id}", "SK": "CREW#latest"}).get("Item")
    if not it:
        return None
    return {k: v for k, v in _clean(it).items() if k not in ("PK", "SK")}


# ---- plans -------------------------------------------------------------------

def put_plan(t, site_id: str, plan: dict, status: str = "sent") -> None:
    t.put_item(Item={"PK": f"SITE#{site_id}", "SK": f"PLAN#{plan['date']}",
                     "plan_json": json.dumps(plan, default=str), "status": status,
                     "plan_hash": plan["plan_hash"], "forecast_run": plan["forecast_issued"],
                     "generated_at": plan["generated_at"]})


def get_plan(t, site_id: str, date: str) -> dict | None:
    it = t.get_item(Key={"PK": f"SITE#{site_id}", "SK": f"PLAN#{date}"}).get("Item")
    if not it:
        return None
    out = _clean(it)
    out["plan"] = json.loads(out.pop("plan_json"))
    return out


def update_plan(t, site_id: str, date: str, **fields) -> None:
    names = {f"#{k}": k for k in fields}
    values = {f":{k}": v for k, v in fields.items()}
    t.update_item(Key={"PK": f"SITE#{site_id}", "SK": f"PLAN#{date}"},
                  UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in fields),
                  ExpressionAttributeNames=names, ExpressionAttributeValues=_num(values))


def claim_idempotency(t, key: str, ttl_days: int = 3) -> bool:
    """True the first time a key is claimed; False on every later attempt."""
    try:
        t.put_item(Item={"PK": f"IDEM#{key}", "SK": "PLAN", "done_at": int(time.time()),
                         "ttl": ttl_in(ttl_days)},
                   ConditionExpression="attribute_not_exists(PK)")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


# ---- overrides, alerts, check-ins -------------------------------------------

def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def put_override(t, site_id: str, date: str, direction: str, reason: str, actor_role: str,
                 decision: str) -> None:
    t.put_item(Item={"PK": f"SITE#{site_id}", "SK": f"OVR#{date}#{_now_iso()}",
                     "direction": direction, "reason": reason, "actor_role": actor_role,
                     "decision": decision})


def put_alert(t, site_id: str, date: str, kind: str, **extra) -> str:
    sk = f"ALERT#{date}#{_now_iso()}"
    t.put_item(Item=_num({"PK": f"SITE#{site_id}", "SK": sk, "kind": kind, "acked_at": None,
                          "ttl": ttl_in(CHECKIN_TTL_DAYS), **extra}))
    return sk


def ack_alert(t, site_id: str, sk: str) -> None:
    t.update_item(Key={"PK": f"SITE#{site_id}", "SK": sk},
                  UpdateExpression="SET acked_at = :a", ExpressionAttributeValues={":a": _now_iso()})


def put_checkin(t, site_id: str, date: str, kind: str, device_hash: str) -> None:
    t.put_item(Item={"PK": f"SITE#{site_id}", "SK": f"CHK#{date}#{_now_iso()}#{device_hash[:6]}",
                     "type": kind, "device_token_hash": device_hash,
                     "ttl": ttl_in(CHECKIN_TTL_DAYS)})


def day_items(t, site_id: str, prefix: str, date: str) -> list[dict]:
    r = t.query(KeyConditionExpression=Key("PK").eq(f"SITE#{site_id}")
                & Key("SK").begins_with(f"{prefix}#{date}"))
    return [_clean(i) for i in r["Items"]]


def rate_limited(t, key_hash: str, limit: int, window_s: int = 60) -> bool:
    """Fixed-window counter. True if this call exceeds `limit` in the window."""
    bucket = int(time.time()) // window_s
    r = t.update_item(Key={"PK": f"RATE#{key_hash}", "SK": str(bucket)},
                      UpdateExpression="ADD n :one SET #ttl = :ttl",
                      ExpressionAttributeNames={"#ttl": "ttl"},
                      ExpressionAttributeValues={":one": 1, ":ttl": int(time.time()) + 2 * window_s},
                      ReturnValues="UPDATED_NEW")
    return int(r["Attributes"]["n"]) > limit


# ---- deletion (/delete_my_data) ---------------------------------------------

def delete_site_data(t, site: dict) -> int:
    """Delete every non-record item for a site. Locked S3 records expire by retention."""
    sid = site["site_id"]
    keys = [{"PK": f"CHAT#{site['owner_hash']}", "SK": "META"},
            {"PK": f"TOKEN#{site['site_token']}", "SK": "META"}]
    kw = {"KeyConditionExpression": Key("PK").eq(f"SITE#{sid}"),
          "ProjectionExpression": "PK, SK"}
    while True:
        r = t.query(**kw)
        keys += [{"PK": i["PK"], "SK": i["SK"]} for i in r["Items"]]
        if "LastEvaluatedKey" not in r:
            break
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
    with t.batch_writer() as b:
        for k in keys:
            b.delete_item(Key=k)
    return len(keys)


def set_site_fields(t, site_id: str, **fields) -> None:
    """Set (value) or remove (None) attributes on the site META item."""
    sets = {k: v for k, v in fields.items() if v is not None}
    removes = [k for k, v in fields.items() if v is None]
    expr = []
    if sets:
        expr.append("SET " + ", ".join(f"#{k} = :{k}" for k in sets))
    if removes:
        expr.append("REMOVE " + ", ".join(f"#{k}" for k in removes))
    kw = {"Key": {"PK": f"SITE#{site_id}", "SK": "META"}, "UpdateExpression": " ".join(expr),
          "ExpressionAttributeNames": {f"#{k}": k for k in fields}}
    if sets:
        kw["ExpressionAttributeValues"] = {f":{k}": v for k, v in sets.items()}
    t.update_item(**kw)


# ---- people (personal / family mode) -------------------------------------------

def put_person(t, owner_hash: str, person: dict) -> None:
    t.put_item(Item=_num({**person, "PK": f"PERSON#{owner_hash}", "SK": "META", "owner_hash": owner_hash,
                          "GSI1PK": "PEOPLE", "GSI1SK": owner_hash}))


def get_person(t, owner_hash: str) -> dict | None:
    it = t.get_item(Key={"PK": f"PERSON#{owner_hash}", "SK": "META"}).get("Item")
    return _clean(it) if it else None


def update_person(t, owner_hash: str, **fields) -> None:
    sets = {k: v for k, v in fields.items() if v is not None}
    removes = [k for k, v in fields.items() if v is None]
    expr = []
    if sets:
        expr.append("SET " + ", ".join(f"#{k} = :{k}" for k in sets))
    if removes:
        expr.append("REMOVE " + ", ".join(f"#{k}" for k in removes))
    kw = {"Key": {"PK": f"PERSON#{owner_hash}", "SK": "META"}, "UpdateExpression": " ".join(expr),
          "ExpressionAttributeNames": {f"#{k}": k for k in fields}}
    if sets:
        kw["ExpressionAttributeValues"] = _num({f":{k}": v for k, v in sets.items()})
    t.update_item(**kw)


def list_people(t) -> list[dict]:
    out, kw = [], {"IndexName": "GSI1", "KeyConditionExpression": Key("GSI1PK").eq("PEOPLE")}
    while True:
        r = t.query(**kw)
        out += [_clean(i) for i in r["Items"]]
        if "LastEvaluatedKey" not in r:
            return out
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]


def delete_person(t, owner_hash: str) -> None:
    t.delete_item(Key={"PK": f"PERSON#{owner_hash}", "SK": "META"})


# ---- community water points (shown after 2 independent reports) -----------------

def report_point(t, area: str, lat: float, lon: float, kind: str, reporter_hash: str) -> int:
    """Add a report; returns the number of distinct reporters for this point (~11 m grid)."""
    pid = f"{lat:.4f}_{lon:.4f}"
    r = t.update_item(Key={"PK": f"PLACE#{area}", "SK": pid},
                      UpdateExpression="ADD reporters :r SET lat = :lat, lon = :lon, kind = :k",
                      ExpressionAttributeValues=_num({":lat": lat, ":lon": lon, ":k": kind})
                      | {":r": {reporter_hash[:16]}},
                      ReturnValues="ALL_NEW")
    return len(r["Attributes"]["reporters"])


def community_points(t, area: str, min_reports: int = 2) -> list[dict]:
    r = t.query(KeyConditionExpression=Key("PK").eq(f"PLACE#{area}"))
    return [{"lat": float(i["lat"]), "lon": float(i["lon"]), "kind": "community_water", "name": "",
             "reports": len(i["reporters"])}
            for i in r["Items"] if len(i.get("reporters", [])) >= min_reports]


# ---- WhatsApp pending messages (held until the user reopens the 24 h window) ------

def add_pending(t, owner_hash: str, body: dict, ttl_days: int = 2) -> None:
    t.put_item(Item={"PK": f"PENDING#{owner_hash}", "SK": f"{time.time():.6f}",
                     "body": json.dumps(body), "ttl": ttl_in(ttl_days)})


def take_pending(t, owner_hash: str) -> list[dict]:
    r = t.query(KeyConditionExpression=Key("PK").eq(f"PENDING#{owner_hash}"))
    items = r["Items"]
    with t.batch_writer() as b:
        for i in items:
            b.delete_item(Key={"PK": i["PK"], "SK": i["SK"]})
    return [json.loads(i["body"]) for i in sorted(items, key=lambda i: i["SK"])]


def claim_once(t, key: str, ttl_s: int) -> bool:
    """True if `key` was not claimed in the last ttl_s seconds (e.g. one re-open template per 12 h)."""
    now = int(time.time())
    try:
        t.put_item(Item={"PK": f"ONCE#{key}", "SK": "X", "ttl": now + ttl_s, "at": now},
                   ConditionExpression="attribute_not_exists(PK) OR #t < :now",
                   ExpressionAttributeNames={"#t": "ttl"}, ExpressionAttributeValues={":now": now})
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
