import base64
import importlib.util
import json
import os
from pathlib import Path

from ihcommon import channels, config, crypto, outbox, repo
from ihcommon.channel import OutsideWindow

KEY = base64.b64encode(os.urandom(32)).decode()


def load(name):
    p = Path(__file__).parents[1] / f"functions/{name}/app.py"
    spec = importlib.util.spec_from_file_location(f"{name}_win", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class WA:
    def __init__(self):
        self.templates, self.texts = [], []

    def send_text(self, chat_id, text, buttons=None):
        raise OutsideWindow("re-engagement")

    def send_template(self, chat_id, name, lang="en_US"):
        self.templates.append((chat_id, name))


def test_held_then_delivered_when_user_replies(ddb_table, monkeypatch):
    monkeypatch.setattr(config, "param", lambda n: KEY)
    wa = WA()
    monkeypatch.setattr(channels, "client_for", lambda c: wa)
    sender = load("sender")
    enc = crypto.encrypt("wa:919999999999", KEY)
    recs = [{"messageId": str(i), "body": json.dumps({"chat_enc": enc, "kind": "text", "text": f"plan {i}"})}
            for i in range(2)]
    assert sender.handler({"Records": recs}, None) == {"batchItemFailures": []}
    assert wa.templates == [("wa:919999999999", "hello_world")]  # one nudge, not two
    owner = crypto.keyed_hash("wa:919999999999", KEY)

    queued = []
    monkeypatch.setattr(outbox, "enqueue", lambda enc_, kind, **kw: queued.append(kw["text"]))
    webhook = load("whatsapp_webhook")
    d = type("D", (), {"t": ddb_table, "key": KEY})()
    webhook.flush_pending(d, "wa:919999999999")
    assert queued == ["plan 0", "plan 1"] and repo.take_pending(ddb_table, owner) == []
