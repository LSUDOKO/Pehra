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
    return get_site(t, it["site_id"]) if it else None


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
