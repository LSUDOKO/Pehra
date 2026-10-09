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
