import base64
import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path

import pytest

from ihcommon import config, repo
from ihcommon.channel import RateLimited
from ihcommon.whatsapp import WhatsApp

KEY = base64.b64encode(os.urandom(32)).decode()
SECRETS = {"whatsapp-app-secret": "appsecret", "whatsapp-verify-token": "verifyme", "data-key": KEY}


class Resp:
    def __init__(self, status, body):
        self.status_code, self._body, self.content = status, body, b"x"

    def json(self):
        return self._body


class Session:
    def __init__(self, *resps):
        self.resps, self.calls = list(resps), []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return self.resps.pop(0) if len(self.resps) > 1 else self.resps[0]


OK = Resp(200, {"messages": [{"id": "wamid.1"}]})


def test_buttons_become_interactive_reply_buttons():
    s = Session(OK)
    buttons = [[("Approve", "ap:d"), ("Override", "ov:d")]]
    WhatsApp("T", "PID", s).send_text("wa:919999999999", "Plan", buttons)
    url, kw = s.calls[0]
    assert url.endswith("/PID/messages") and kw["json"]["to"] == "919999999999"
    btns = kw["json"]["interactive"]["action"]["buttons"]
    assert [b["reply"]["id"] for b in btns] == ["ap:d", "ov:d"]


def test_long_plan_sent_then_short_button_prompt():
    s = Session(OK)
    WhatsApp("T", "PID", s).send_text("wa:91", "x" * 1500, [[("Approve", "ap:d")]])
    assert s.calls[0][1]["json"]["type"] == "text" and s.calls[1][1]["json"]["type"] == "interactive"


def test_pair_rate_limit_raises():
    s = Session(Resp(400, {"error": {"code": 131056, "message": "pair rate limit"}}))
    with pytest.raises(RateLimited):
        WhatsApp("T", "PID", s).send_text("wa:91", "hi")


# ---- webhook ---------------------------------------------------------------------

def load_app():
    p = Path(__file__).parents[1] / "functions/whatsapp_webhook/app.py"
    spec = importlib.util.spec_from_file_location("wa_app", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Bot:
    def __init__(self):
        self.sent = []

    def send_text(self, chat_id, text, buttons=None):
        self.sent.append((chat_id, text, buttons))

    def answer_button(self, *_a):
        pass


@pytest.fixture
def wa(ddb_table, monkeypatch):
    app = load_app()
    d = app.Deps.__new__(app.Deps)
    d.t, d.bot, d.key, d.sfn, d.lam = ddb_table, Bot(), KEY, None, None
    monkeypatch.setattr(app, "_deps", d)
    monkeypatch.setattr(config, "param", lambda n: SECRETS[n])
    return app, d


def post(app, payload, secret="appsecret"):
    body = json.dumps(payload)
    sig = "sha256=" + hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return app.handler({"requestContext": {"http": {"method": "POST"}, "domainName": "x.example"},
                        "headers": {"X-Hub-Signature-256": sig}, "body": body}, None)


def text_msg(text, frm="919876543210"):
    return {"entry": [{"changes": [{"value": {"messages": [
        {"from": frm, "id": "wamid.a", "type": "text", "text": {"body": text}}]}}]}]}


def test_verify_handshake(wa):
    app, _ = wa
    ok = app.handler({"requestContext": {"http": {"method": "GET"}}, "queryStringParameters": {
        "hub.mode": "subscribe", "hub.verify_token": "verifyme", "hub.challenge": "42"}}, None)
    bad = app.handler({"requestContext": {"http": {"method": "GET"}}, "queryStringParameters": {
        "hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "42"}}, None)
    assert ok["body"] == "42" and bad["statusCode"] == 403


def test_bad_signature_rejected(wa):
    app, d = wa
    assert post(app, text_msg("hi"), secret="wrong")["statusCode"] == 401 and not d.bot.sent


def test_register_and_call_on_with_own_number(wa):
    app, d = wa
    post(app, text_msg("/register Ramesh Tower, Chennai"))
    site = repo.list_sites(d.t)[0]
    assert site["city"] == "chennai" and "919876543210" not in json.dumps(site)
    post(app, text_msg("/call_on"))
    assert "3210" in d.bot.sent[-1][1] and repo.get_site(d.t, site["site_id"])["call_enc"]


def test_button_reply_becomes_callback(wa):
    app, d = wa
    post(app, text_msg("/register Site B, Delhi"))
    payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "919876543210", "id": "wamid.b",
               "type": "interactive", "interactive": {"type": "button_reply",
               "button_reply": {"id": "ov:2026-10-11", "title": "Override"}}}]}}]}]}
    post(app, payload)
    assert d.bot.sent[-1][1] == "Plan ko kaise badalna hai?"


def test_outside_24h_window_is_its_own_error():
    from ihcommon.channel import OutsideWindow
    s = Session(Resp(400, {"error": {"code": 131047, "message": "Re-engagement message"}}))
    with pytest.raises(OutsideWindow):
        WhatsApp("T", "PID", s).send_text("wa:91", "plan")


def test_not_allowed_recipient_is_permanent():
    from ihcommon.channel import PermanentError
    s = Session(Resp(400, {"error": {"code": 131030, "message": "not in allowed list"}}))
    with pytest.raises(PermanentError):
        WhatsApp("T", "PID", s).send_text("wa:91", "hi")
