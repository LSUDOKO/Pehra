import importlib.util
from datetime import UTC, datetime
from pathlib import Path

from ihcommon import outbox, people, repo


def load():
    p = Path(__file__).parents[1] / "functions/personal_fanout/app.py"
    spec = importlib.util.spec_from_file_location("pf_app", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_family_call_once_per_day_on_high_days(ddb_table, monkeypatch):
    app, sent = load(), []
    repo.put_person(ddb_table, "o1", {"place": "Delhi", "lat": 28.6, "lon": 77.2, "chat_enc": "C",
                                      "family_enc": "F", "household": {"elderly": 1}})
    repo.put_person(ddb_table, "o2", {"place": "Delhi", "lat": 28.6, "lon": 77.2, "chat_enc": "D"})
    monkeypatch.setattr(people, "today", lambda p, now=None: {
        "text": "msg", "forecast": {"overall_level": "khatarnak"}, "call_text": "Namaste..."})
    monkeypatch.setattr(outbox, "enqueue", lambda enc, kind, **kw: sent.append((enc, kind)))
    monkeypatch.setattr(app, "datetime", type("D", (), {"now": staticmethod(lambda tz=None: datetime(2026, 5, 1, 1, 30, tzinfo=UTC))}))
    out = app.handler({}, None)
    assert out == {"sent": 2, "family_calls": 1}
    assert ("F", "call") in sent and sent.count(("C", "text")) == 1
    sent.clear()
    assert app.handler({}, None)["family_calls"] == 0  # not twice on the same day
