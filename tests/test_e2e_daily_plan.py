"""End to end, offline: heat store -> plan_step build -> send -> nightly record -> verify chain.

Uses moto for DynamoDB, S3 and SQS, the recorded Kharghar ERA5 day as the 'forecast',
and the template fallback (AGENT_ENABLED=false, Polly stubbed out).
"""

import base64
import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path

import boto3
import pytest

from heatcore.heat import compute_heat, heat_to_json
from heatcore.openmeteo import parse_hourly
from ihcommon import config, crypto, heatstore, repo, voice
from ihcommon.records import verify_chain

ROOT = Path(__file__).parents[1]
KEY = base64.b64encode(os.urandom(32)).decode()
DAY = "2023-04-16"


def load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_app", ROOT / f"functions/{name}/app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def aws(ddb_table, monkeypatch):
    s3 = boto3.client("s3", region_name="ap-south-1")
    for b in ("heat", "media", "records"):
        s3.create_bucket(Bucket=b, CreateBucketConfiguration={"LocationConstraint": "ap-south-1"})
    q = boto3.client("sqs", region_name="ap-south-1").create_queue(QueueName="out")["QueueUrl"]
    for k, v in {"HEAT_BUCKET": "heat", "MEDIA_BUCKET": "media", "RECORDS_BUCKET": "records",
                 "OUT_QUEUE_URL": q, "AGENT_ENABLED": False}.items():
        monkeypatch.setattr(config, k, v)
    monkeypatch.setattr(config, "param", lambda n: KEY)
    monkeypatch.setattr(voice, "synthesize", lambda text: b"OggS-fake")
    return s3, q


def test_daily_plan_end_to_end(aws, ddb_table, monkeypatch):
    s3, q = aws
    rows = parse_hourly(json.loads((ROOT / "tests/fixtures/openmeteo_kharghar_2023-04-16.json").read_text()))
    heat = compute_heat(rows, 19.04, 73.07)
    doc = {"city": "kharghar", "run_id": "R1", "model": "ERA5 replay",
           "issued_at": "2023-04-15T06:30:00+00:00", "hours": heat_to_json(heat)}
    heatstore.put_heat("kharghar", "R1", doc)
    site = {"site_id": "s1", "name": "Kharghar ground", "city": "kharghar", "lat": 19.04, "lon": 73.07,
            "site_token": "tok-e2e-0001", "tenant_id": "default"}
    repo.put_site(ddb_table, site, "owner", crypto.encrypt("4242", KEY))
    repo.put_crew(ddb_table, "s1", DAY, {"headcount": 40, "heavy_count": 10, "new_count": 3, "new_day": 1})

    step = load("plan_step")
    monkeypatch.setattr(step.planning, "now_ist", lambda: datetime(2023, 4, 15, 19, 0))
    built = step.handler({"action": "build", "site_id": "s1", "date": DAY, "mode": "scheduled"}, None)
    assert built["skip"] is False and "Kaam band" in built["text"] and built["voice_key"]
    assert step.handler({"action": "build", "site_id": "s1", "date": DAY, "mode": "scheduled"}, None)["skip"]

    step.handler({"action": "send", **built}, None)
    msgs = boto3.client("sqs", region_name="ap-south-1").receive_message(QueueUrl=q, MaxNumberOfMessages=10)
    bodies = [json.loads(m["Body"]) for m in msgs["Messages"]]
    assert {b["kind"] for b in bodies} == {"text", "voice"}
    text = next(b for b in bodies if b["kind"] == "text")
    assert text["buttons"][0][0][1] == f"ap:{DAY}" and crypto.decrypt(text["chat_enc"], KEY) == "4242"

    plan = repo.get_plan(ddb_table, "s1", DAY)["plan"]
    assert plan["stop_from"] == 11 and plan["new_workers"]["count"] == 3 and plan["water"]["cans_20l"] > 0

    repo.update_plan(ddb_table, "s1", DAY, status="approved")
    nightly = load("nightly_record")
    out = nightly.handler({"date": DAY}, None)
    assert out["results"][0]["result"] == "locked"
    rec = json.loads(s3.get_object(Bucket="records", Key=f"records/s1/{DAY}.json")["Body"].read())
    assert rec["plan_status"] == "approved" and verify_chain([rec]) == []
