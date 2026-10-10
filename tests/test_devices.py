import base64
import importlib.util
import json
import os
import re
from pathlib import Path

import pytest

from ihcommon import config, devices, outbox, repo

KEY = base64.b64encode(os.urandom(32)).decode()
SITE = {"site_id": "s1", "name": "Site A", "city": "chennai", "lat": 13.08, "lon": 80.27,
        "site_token": "tok-abcdefgh", "tenant_id": "t1"}


def load(name):
    p = Path(__file__).parents[1] / f"functions/{name}/app.py"
    spec = importlib.util.spec_from_file_location(f"{name}_dev", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def web(ddb_table, monkeypatch):
    monkeypatch.setattr(config, "param", lambda n: KEY)
    sent, calls = [], []
    monkeypatch.setattr(outbox, "enqueue", lambda enc, kind, **kw: sent.append((kind, kw.get("text", ""))))
    monkeypatch.setattr(outbox, "enqueue_call", lambda site, speech: calls.append(speech) or True)
    # forecast for the current hour: WBGT 31.0 in the sun, moderate wind and sun
    monkeypatch.setattr(devices, "_forecast_hour",
                        lambda lat, lon, now: ({"pressure": 1005, "wind": 2, "ghi": 800, "direct": 550}, 31.0))
    repo.put_site(ddb_table, SITE, "owner", "enc")
    app = load("public_web")
    app.sent, app.calls = sent, calls
    return app


def post(app, body, ip="9.9.9.9"):
    r = app.handler({"rawPath": "/api/sensor", "body": json.dumps(body),
                     "requestContext": {"http": {"method": "POST", "sourceIp": ip}}}, None)
    return r["statusCode"], json.loads(r["body"])


def test_weather_sensor_hotter_than_forecast_alerts_once(web, ddb_table):
    tok = devices.register(ddb_table, "site", "s1", "weather", 13.08, 80.27, "enc", 100, KEY)
    code, out = post(web, {"device_token": tok, "temp_c": 39, "rh": 65})
    assert code == 200 and out["alert"] and out["notified"] and out["site_wbgt_sun"] > 31.0
    code, out = post(web, {"device_token": tok, "temp_c": 39, "rh": 65})
    assert out["alert"] and "notified" not in out  # rate-limited per device
    assert [k for k, _ in web.sent] == ["text"] and "Site sensor" in web.sent[0][1]


def test_tank_low_and_drain_high_with_call(web, ddb_table):
    tank = devices.register(ddb_table, "site", "s1", "tank", 13.08, 80.27, "enc", 120, KEY)
    assert post(web, {"device_token": tank, "distance_cm": 110})[1]["tank_pct"] == 8
    drain = devices.register(ddb_table, "site", "s1", "drain", 13.08, 80.27, "enc", 100, KEY)
    code, out = post(web, {"device_token": drain, "distance_cm": 60})
    assert out["water_cm"] == 40 and out["alert"] and web.calls
    assert any("tanki" in t for _, t in web.sent)


def test_bad_inputs(web, ddb_table):
    assert post(web, {"device_token": "nope"})[0] == 400
    assert post(web, {"device_token": "dev_unknown"})[0] == 404
    tok = devices.register(ddb_table, "site", "s1", "weather", 13.08, 80.27, "enc", 100, KEY)
    assert post(web, {"device_token": tok, "temp_c": "hot"})[0] == 400


def test_device_page_and_bot_registration(web, ddb_table, monkeypatch):
    from tests.test_webhook import Bot, Lam, Sfn, load_app
    app = load_app()
    d = app.Deps.__new__(app.Deps)
    d.t, d.bot, d.key, d.sfn, d.lam = ddb_table, Bot(), KEY, Sfn(), Lam()
    monkeypatch.setattr(app, "_deps", d)
    monkeypatch.setattr(config, "PUBLIC_BASE_URL", "https://api.example")
    repo.put_site(ddb_table, SITE, __import__("ihcommon.crypto", fromlist=["x"]).keyed_hash("111", KEY), "enc")
    body = {"message": {"chat": {"id": 111}, "text": "/device tank 120"}}
    app.handler({"headers": {"X-Telegram-Bot-Api-Secret-Token": KEY}, "body": json.dumps(body)}, None)
    token = re.search(r"(dev_[\w-]+)", d.bot.sent[-1][1]).group(1)
    assert "https://api.example/device/" in d.bot.sent[-1][1]
    page = web.handler({"rawPath": f"/device/{token}", "requestContext": {"http": {"method": "GET"}}}, None)
    assert page["statusCode"] == 200 and "Water tank" in page["body"]
