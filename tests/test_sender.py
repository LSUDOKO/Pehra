import base64
import importlib.util
import json
import os
from pathlib import Path

from ihcommon import channels, config, crypto, voicecall

KEY = base64.b64encode(os.urandom(32)).decode()


def load():
    p = Path(__file__).parents[1] / "functions/sender/app.py"
    spec = importlib.util.spec_from_file_location("sender_app", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Client:
    def __init__(self, name, log):
        self.name, self.log = name, log

    def send_text(self, chat_id, text, buttons=None):
        self.log.append((self.name, chat_id, text, buttons))


def test_routes_by_channel_and_calls(monkeypatch):
    app, log, calls = load(), [], []
    monkeypatch.setattr(config, "param", lambda n: KEY)
    monkeypatch.setattr(channels, "client_for",
                        lambda c: Client("whatsapp" if channels.is_whatsapp(c) else "telegram", log))
    monkeypatch.setattr(voicecall, "alert_call", lambda phone, msg: calls.append((phone, msg["text"])))
    monkeypatch.setattr(app, "WHATSAPP_PAIR_GAP_S", 0)
    recs = [{"messageId": str(i), "body": json.dumps(b)} for i, b in enumerate([
        {"chat_enc": crypto.encrypt("12345", KEY), "kind": "text", "text": "tg", "buttons": []},
        {"chat_enc": crypto.encrypt("wa:9199", KEY), "kind": "text", "text": "wa",
         "buttons": [[["Approve", "ap:d"]]]},
        {"chat_enc": crypto.encrypt("+919876543210", KEY), "kind": "call", "text": "Dhyan dein"},
    ])]
    assert app.handler({"Records": recs}, None) == {"batchItemFailures": []}
    assert [entry[0] for entry in log] == ["telegram", "whatsapp"]
    assert log[1][3] == [[("Approve", "ap:d")]] and calls == [("+919876543210", "Dhyan dein")]
