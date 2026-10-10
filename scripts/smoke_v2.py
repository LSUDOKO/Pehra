"""Smoke test the v2 features on the deployed stack (no real person is contacted).

    uv run python scripts/smoke_v2.py

Uses chats addressed to "test:" which the sender drops. Checks: personal forecast for a city and for
an on-demand tile, the water finder, the 07:00 fan-out Lambda, and a weather + drain sensor through
the public API. Cleans up afterwards.
"""

import json
import os
import secrets
import sys
import urllib.request
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parents[1]))

STACK, REGION = "invisible-heat", "ap-south-1"


def main() -> None:
    cfn = boto3.client("cloudformation", region_name=REGION)
    out = {o["OutputKey"]: o["OutputValue"] for o in cfn.describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]}
    os.environ.update({"TABLE_NAME": f"{STACK}-table", "HEAT_BUCKET": out["HeatBucketName"], "AWS_REGION": REGION})
    from ihcommon import config, crypto, devices, people, repo  # after env is set
    key = config.param("data-key")
    t = repo.table()

    owners = []
    for place, lat, lon in (("Delhi", 28.6139, 77.2090), ("Varanasi (tile)", 25.3176, 83.0106)):
        owner = "smoke-" + secrets.token_hex(6)
        owners.append(owner)
        repo.put_person(t, owner, {"place": place, "lat": lat, "lon": lon,
                                   "chat_enc": crypto.encrypt(f"test:{owner}", key),
                                   "household": {"adults": 2, "elderly": 1, "young_children": 1, "works_outdoors": True}})
        r = people.today(repo.get_person(t, owner))
        print(f"\n== Personal forecast: {place} (level {r['forecast']['overall_level']}, "
              f"family call: {'yes' if r['call_text'] else 'no'})\n{r['text']}")

    print("\n== Water finder near Connaught Place, Delhi\n" + people.find_water(t, 28.6315, 77.2167))

    lam = boto3.client("lambda", region_name=REGION)
    fn = next(f["FunctionName"] for p in lam.get_paginator("list_functions").paginate() for f in p["Functions"]
              if f["FunctionName"].startswith(f"{STACK}-PersonalFanout"))
    res = json.loads(lam.invoke(FunctionName=fn, Payload=b"{}")["Payload"].read())
    print("\n== 07:00 personal fan-out Lambda:", res)

    site_like = "smoke-dev-" + secrets.token_hex(4)
    toks = {k: devices.register(t, "person", site_like, k, 13.08, 80.27, crypto.encrypt("test:dev", key), 100, key)
            for k in ("weather", "drain")}
    for kind, body in (("weather", {"temp_c": 39.5, "rh": 70}), ("drain", {"distance_cm": 55})):
        req = urllib.request.Request(out["ApiUrl"] + "/api/sensor", method="POST",
                                     headers={"content-type": "application/json"},
                                     data=json.dumps({"device_token": toks[kind], **body}).encode())
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"== Sensor {kind}: {r.status} {r.read().decode()}")
    with urllib.request.urlopen(out["ApiUrl"] + f"/device/{toks['weather']}", timeout=20) as r:
        print("== Simulator page:", r.status)

    for owner in owners:
        repo.delete_person(t, owner)
    for tok in toks.values():
        th, _ = devices.get_device(t, tok, key)
        t.delete_item(Key={"PK": f"DEVICE#{th}", "SK": "META"})
    print("\ncleaned up")


if __name__ == "__main__":
    main()
