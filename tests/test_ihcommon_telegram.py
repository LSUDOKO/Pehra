import pytest

from ihcommon.channel import RateLimited
from ihcommon.telegram import Telegram


class Resp:
    def __init__(self, status, body):
        self.status_code, self._body, self.content = status, body, b"x"

    def json(self):
        return self._body


class Session:
    def __init__(self, resp):
        self.resp, self.calls = resp, []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return self.resp


def test_send_text_with_buttons():
    s = Session(Resp(200, {"ok": True, "result": {"message_id": 7}}))
    out = Telegram("T", s).send_text("42", "hi", [[("Approve", "ap:1")]])
    url, kw = s.calls[0]
    assert url.endswith("/botT/sendMessage") and out["message_id"] == 7
    assert kw["json"]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "ap:1"


def test_rate_limit_raises_with_retry_after():
    s = Session(Resp(429, {"ok": False, "parameters": {"retry_after": 11}}))
    with pytest.raises(RateLimited) as e:
        Telegram("T", s).send_text("42", "hi")
    assert e.value.retry_after == 11


def test_error_raises():
    with pytest.raises(RuntimeError):
        Telegram("T", Session(Resp(400, {"ok": False, "description": "bad"}))).send_text("1", "x")
