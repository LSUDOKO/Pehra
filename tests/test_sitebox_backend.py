import base64
import importlib.util
import json
import os
import re
from pathlib import Path

import pytest

from ihcommon import boxes, config, outbox, repo

KEY = base64.b64encode(os.urandom(32)).decode()


def load():
    p = Path(__file__).parents[1] / "functions/iot_box/app.py"
    spec = importlib.util.spec_from_file_location("iot_box_app", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def env(ddb_table, monkeypatch):
    monkeypatch.setattr(config, "param", lambda n: KEY)
    monkeypatch.setattr(config, "PUBLIC_BASE_URL", "https://api.example")
    sent, calls = [], []
    monkeypatch.setattr(outbox, "enqueue", lambda enc, kind, **kw: sent.append(kw.get("text", "")))
    monkeypatch.setattr(outbox, "enqueue_call", lambda site, speech: calls.append(speech) or True)
    monkeypatch.setattr(boxes, "_forecast", lambda lat, lon, now: ({"pressure": 1005, "wind": 2, "ghi": 800}, 30.0))
    repo.put_site(ddb_table, {"site_id": "s1", "name": "Site A", "city": "chennai", "lat": 13.08, "lon": 80.27,
                              "site_token": "tok-x", "tenant_id": "t"}, "own", "enc")
    b = boxes.register(ddb_table, "site", "s1", 13.08, 80.27, "enc", "Site A", KEY)
    app = load()
    published = []
    monkeypatch.setattr(app, "_iot_data", lambda: type("C", (), {"publish": lambda self, **kw: published.append(kw)})())
    return app, b, sent, calls, published


HOT = {"temp_c": 38, "rh": 65, "globe_c": 47, "light_raw": 3900, "tank_distance_cm": 100, "drain_distance_cm": 80}


def http(app, method, path, body=None):
    ev = {"rawPath": path, "requestContext": {"http": {"method": method}, "domainName": "api.example"},
          "body": json.dumps(body) if body is not None else None}
    r = app.handler(ev, None)
    return r["statusCode"], (json.loads(r["body"]) if r["headers"]["content-type"].startswith("application/json") else r["body"])


def test_iot_rule_event_publishes_command(env):
    app, b, sent, calls, published = env
    out = app.handler({"box_id": b["box_id"], **HOT}, None)
    assert out["ok"] and published[0]["topic"] == f"pehra/box/{b['box_id']}/cmd"
    state = json.loads(published[0]["payload"])
    assert state["fan_on"] and state["pump_on"] and state["level_index"] == 4
    assert any("tanki" in s for s in sent) and any("garam" in s for s in sent)


def test_https_fallback_and_twin_state(env):
    app, b, sent, calls, _ = env
    code, st = http(app, "POST", "/api/box", {"token": b["device_token"], **HOT, "sos": True})
    assert code == 200 and st["sos_active"] and calls  # SOS rings the supervisor
    code, twin = http(app, "GET", f"/api/box/{b['view_token']}/state")
    assert code == 200 and twin["wbgt_c"] == st["wbgt_c"]
    assert http(app, "GET", f"/api/box/{b['device_token']}/state")[0] == 404  # device token is not a view token


def test_alerts_rate_limited_and_bad_input(env):
    app, b, sent, _, _ = env
    http(app, "POST", "/api/box", {"token": b["device_token"], **HOT})
    n = len(sent)
    http(app, "POST", "/api/box", {"token": b["device_token"], **HOT})
    assert len(sent) == n
    assert http(app, "POST", "/api/box", {"token": b["device_token"], "rh": 50})[0] == 400
    assert http(app, "POST", "/api/box", {"token": "nope"})[0] == 400


def test_bot_registers_box(env, ddb_table, monkeypatch):
    from tests.test_webhook import Bot, Lam, Sfn, load_app
    wh = load_app()
    d = wh.Deps.__new__(wh.Deps)
    d.t, d.bot, d.key, d.sfn, d.lam = ddb_table, Bot(), KEY, Sfn(), Lam()
    monkeypatch.setattr(wh, "_deps", d)
    from ihcommon import crypto
    repo.put_site(ddb_table, {"site_id": "s2", "name": "Site B", "city": "delhi", "lat": 28.6, "lon": 77.2,
                              "site_token": "tok-y", "tenant_id": "t"}, crypto.keyed_hash("555", KEY), "enc2")
    wh.handler({"headers": {"X-Telegram-Bot-Api-Secret-Token": KEY},
                "body": json.dumps({"message": {"chat": {"id": 555}, "text": "/device box"}})}, None)
    msg = d.bot.sent[-1][1]
    assert "Site Box" in msg and re.search(r"/twin/view_", msg)
