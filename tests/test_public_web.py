import base64
import importlib.util
import json
import os
from pathlib import Path

import pytest

from ihcommon import config, outbox, repo

KEY = base64.b64encode(os.urandom(32)).decode()
SITE = {"site_id": "s1", "name": "Site A", "city": "chennai", "lat": 13.08, "lon": 80.27,
        "site_token": "tok-abcdefgh", "tenant_id": "t1"}


def load_app():
    p = Path(__file__).parents[1] / "functions/public_web/app.py"
    spec = importlib.util.spec_from_file_location("public_web_app", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def app(ddb_table, monkeypatch):
    monkeypatch.setattr(config, "param", lambda n: KEY)
    sent = []
    monkeypatch.setattr(outbox, "enqueue", lambda *a, **k: sent.append(k))
    repo.put_site(ddb_table, SITE, "owner", "enc")
    mod = load_app()
    mod.sent = sent
    return mod


def post(app, body, ip="1.2.3.4"):
    return app.handler({"rawPath": "/api/checkin", "body": json.dumps(body),
                        "requestContext": {"http": {"method": "POST", "sourceIp": ip}}}, None)


def ev(kind, dev="device-0001", token="tok-abcdefgh"):
    return {"type": kind, "site_token": token, "device_token": dev}


def test_break_logged_without_names(app, ddb_table):
    assert post(app, ev("break_start"))["statusCode"] == 200
    items = repo.day_items(ddb_table, "s1", "CHK", "")
    assert len(items) == 1 and "device-0001" not in json.dumps(items)


def test_symptom_alerts_supervisor_and_dedupes(app):
    r = post(app, ev("symptom"))
    assert r["statusCode"] == 200 and "108" in json.loads(r["body"])["first_aid"]
    post(app, ev("symptom"))
    assert len(app.sent) == 1 and "chakkar" in app.sent[0]["text"]


def test_rate_limit_per_device(app):
    codes = [post(app, ev("break_start"))["statusCode"] for _ in range(12)]
    assert codes[:10] == [200] * 10 and codes[-1] == 429


def test_unknown_token_and_bad_type(app):
    assert post(app, ev("break_start", token="nope"))["statusCode"] == 404
    assert post(app, ev("dance"))["statusCode"] == 400


def test_worker_page_served(app):
    r = app.handler({"rawPath": "/s/tok-abcdefgh", "requestContext": {"http": {"method": "GET"}}}, None)
    assert r["statusCode"] == 200 and "Aaram shuru" in r["body"] and "Site A" in r["body"]
