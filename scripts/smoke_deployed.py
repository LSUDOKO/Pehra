"""Smoke test the deployed stack without Telegram (nothing is sent to anyone).

    uv run python scripts/smoke_deployed.py [--stack invisible-heat] [--keep]

Seeds a demo site, builds tomorrow's plan through the real plan Lambda (AI intro + Polly),
loads the worker page and poster, logs a break, locks a nightly record, verifies the
hash chain from S3, then removes the demo site (locked records stay until retention ends).
"""

import argparse
import json
import secrets
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parents[1]))

from ihcommon.records import verify_chain  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))


def fn_name(lam, stack: str, logical: str) -> str:
    for page in lam.get_paginator("list_functions").paginate():
        for f in page["Functions"]:
            if f["FunctionName"].startswith(f"{stack}-{logical}"):
                return f["FunctionName"]
    raise SystemExit(f"function {logical} not found")


def invoke(lam, name: str, payload: dict) -> dict:
    r = lam.invoke(FunctionName=name, Payload=json.dumps(payload).encode())
    out = json.loads(r["Payload"].read())
    if r.get("FunctionError"):
        raise SystemExit(f"{name} failed: {out}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack", default="invisible-heat")
    ap.add_argument("--region", default="ap-south-1")
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    cfn = boto3.client("cloudformation", region_name=a.region)
    out = {o["OutputKey"]: o["OutputValue"] for o in cfn.describe_stacks(StackName=a.stack)["Stacks"][0]["Outputs"]}
    lam = boto3.client("lambda", region_name=a.region)
    ddb = boto3.resource("dynamodb", region_name=a.region).Table(f"{a.stack}-table")
    s3 = boto3.client("s3", region_name=a.region)

    site_id, token = f"smoke-{secrets.token_hex(3)}", secrets.token_urlsafe(16)
    site = {"site_id": site_id, "name": "Smoke test site", "city": "chennai", "lat": 13.08, "lon": 80.27,
            "site_token": token, "tenant_id": "default"}
    owner = "smoke-" + secrets.token_hex(8)
    ddb.put_item(Item={**{k: str(v) for k, v in site.items()}, "PK": f"SITE#{site_id}", "SK": "META",
                       "owner_hash": owner, "chat_enc": "none", "GSI1PK": "SMOKE", "GSI1SK": site_id})
    ddb.put_item(Item={"PK": f"TOKEN#{token}", "SK": "META", "site_id": site_id})
    for sk in ("CREW#latest",):
        ddb.put_item(Item={"PK": f"SITE#{site_id}", "SK": sk, "headcount": 40, "heavy_count": 10,
                           "new_count": 3, "new_day": 1})
    print("1. seeded", site_id)

    today = datetime.now(IST).date()
    plan_step = fn_name(lam, a.stack, "PlanStepFunction")
    built = invoke(lam, plan_step, {"action": "build", "site_id": site_id, "date": today.isoformat(),
                                    "mode": "on_demand"})
    print("2. plan built; voice:", bool(built["voice_key"]))
    print("   " + built["text"].replace("\n", "\n   "))

    base = out["ApiUrl"]
    for path in (f"/s/{token}", f"/p/{token}", "/audit"):
        with urllib.request.urlopen(base + path, timeout=20) as r:
            print(f"3. GET {path} -> {r.status}")
    req = urllib.request.Request(base + "/api/checkin", method="POST", headers={"content-type": "application/json"},
                                 data=json.dumps({"site_token": token, "device_token": "smoke-device-01",
                                                  "type": "break_start"}).encode())
    with urllib.request.urlopen(req, timeout=20) as r:
        print("4. break logged ->", r.status)

    ddb.update_item(Key={"PK": f"SITE#{site_id}", "SK": f"PLAN#{today}"},
                    UpdateExpression="SET #s = :s", ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":s": "approved"})
    rec_fn = fn_name(lam, a.stack, "NightlyRecordFunction")
    # the nightly function iterates registered sites (GSI1PK=SITES); lock just the smoke site here
    ddb.update_item(Key={"PK": f"SITE#{site_id}", "SK": "META"}, UpdateExpression="SET GSI1PK = :p",
                    ExpressionAttributeValues={":p": "SITES"})
    res = invoke(lam, rec_fn, {"date": today.isoformat()})
    print("5. nightly record:", [r["result"] for r in res["results"]])
    key = f"records/{site_id}/{today}.json"
    rec = json.loads(s3.get_object(Bucket=out["RecordsBucketName"], Key=key)["Body"].read())
    lock = s3.get_object_retention(Bucket=out["RecordsBucketName"], Key=key)["Retention"]
    print(f"6. record locked ({lock['Mode']} until {lock['RetainUntilDate']:%Y-%m-%d}); "
          f"chain problems: {verify_chain([rec]) or 'none'}")

    if not a.keep:
        r = ddb.query(KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(f"SITE#{site_id}"))
        with ddb.batch_writer() as b:
            for i in r["Items"]:
                b.delete_item(Key={"PK": i["PK"], "SK": i["SK"]})
            b.delete_item(Key={"PK": f"TOKEN#{token}", "SK": "META"})
        print("7. demo site removed")


if __name__ == "__main__":
    main()
