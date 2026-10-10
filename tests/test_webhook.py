import base64
import importlib.util
import json
import os
from pathlib import Path

import pytest

from ihcommon import config, crypto, repo

KEY = base64.b64encode(os.urandom(32)).decode()


def load_app():
    p = Path(__file__).parents[1] / "functions/telegram_webhook/app.py"
    spec = importlib.util.spec_from_file_location("webhook_app", p)
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


class Sfn:
    def __init__(self):
        self.success, self.started = [], []

    def send_task_success(self, **kw):
        self.success.append(kw)

    def start_execution(self, **kw):
        self.started.append(kw)


class Lam:
    def __init__(self):
        self.calls = []

    def invoke(self, **kw):
        self.calls.append(json.loads(kw["Payload"]))


@pytest.fixture
def env(ddb_table, monkeypatch):
    app = load_app()
    d = app.Deps.__new__(app.Deps)
    d.t, d.bot, d.key, d.sfn, d.lam = ddb_table, Bot(), KEY, Sfn(), Lam()
    monkeypatch.setattr(app, "_deps", d)
    secrets = {"webhook-secret": "s3cret", "data-key": KEY, "telegram-token": "x"}
    monkeypatch.setattr(config, "param", lambda n: secrets[n])
    return app, d


def msg(app, text, chat=111, secret="s3cret"):
    body = {"message": {"chat": {"id": chat}, "text": text}}
    return app.handler({"headers": {"X-Telegram-Bot-Api-Secret-Token": secret},
                        "body": json.dumps(body)}, None)


def tap(app, data, chat=111):
    body = {"callback_query": {"id": "cb", "data": data, "message": {"chat": {"id": chat}}}}
    return app.handler({"headers": {"X-Telegram-Bot-Api-Secret-Token": "s3cret"},
                        "body": json.dumps(body)}, None)


def register(app, d):
    msg(app, "/register Ramesh Tower, Chennai")
    return repo.list_sites(d.t)[0]


def test_rejects_bad_secret(env):
    app, d = env
    assert msg(app, "/start", secret="nope")["statusCode"] == 401 and not d.bot.sent


def test_register_stores_hashed_chat_only(env):
    app, d = env
    site = register(app, d)
    assert site["city"] == "chennai"
    assert all(v not in ("111", 111) for v in site.values())  # chat id never stored in clear
    assert crypto.decrypt(site["chat_enc"], KEY) == "111"
    assert "QR page" in d.bot.sent[-1][1]


def test_crew_text_needs_confirmation(env):
    app, d = env
    site = register(app, d)
    msg(app, "40 log, 10 bhaari kaam, 3 naye aaye")
    assert d.bot.sent[-1][1].endswith("Sahi hai?") and repo.get_crew(d.t, site["site_id"]) is None
    tap(app, "crew_ok")
    assert repo.get_crew(d.t, site["site_id"])["headcount"] == 40


def seed_plan(d, site_id, day="2026-10-11"):
    repo.put_plan(d.t, site_id, {"date": day, "plan_hash": "h", "forecast_issued": "x",
                                  "generated_at": "y"})
    repo.update_plan(d.t, site_id, day, task_token="TOKEN")


def test_approve_resumes_state_machine(env):
    app, d = env
    site = register(app, d)
    seed_plan(d, site["site_id"])
    tap(app, "ap:2026-10-11")
    assert d.sfn.success[0]["taskToken"] == "TOKEN"
    assert repo.get_plan(d.t, site["site_id"], "2026-10-11")["status"] == "approved"


def test_looser_override_needs_real_reason(env):
    app, d = env
    site = register(app, d)
    seed_plan(d, site["site_id"])
    tap(app, "ovl:2026-10-11")
    msg(app, "late")
    assert "chhota" in d.bot.sent[-1][1] and not d.sfn.success
    msg(app, "Client inspection at noon, crew in shade")
    assert json.loads(d.sfn.success[0]["output"])["direction"] == "looser"
    assert repo.get_plan(d.t, site["site_id"], "2026-10-11")["status"] == "overridden"


def test_questions_go_to_async_assistant(env):
    app, d = env
    register(app, d)
    msg(app, "Kya hum 2 baje concrete daal sakte hain?")
    assert d.lam.calls[0]["kind"] == "question"


def test_unregistered_chat_is_told_to_register(env):
    app, d = env
    msg(app, "hello", chat=999)
    assert "/register" in d.bot.sent[-1][1]


def test_delete_my_data(env):
    app, d = env
    register(app, d)
    tap(app, "del_yes")
    assert repo.list_sites(d.t) == []
