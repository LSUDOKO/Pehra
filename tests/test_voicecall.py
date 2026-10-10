import pytest

from ihcommon import config, voicecall


@pytest.mark.parametrize("raw, out", [
    ("+91 98765-43210", "+919876543210"), ("919876543210", "+919876543210"),
    ("wa:919876543210", "+919876543210"), ("09876543210", "+919876543210"),
    ("9876543210", "+919876543210"), ("12", None),
])
def test_normalise_phone(raw, out):
    assert voicecall.normalise_phone(raw) == out


def test_twiml_escapes_presigned_url():
    doc = voicecall.twiml("https://b.s3/a.mp3?X=1&Y=2")
    assert "&amp;Y=2" in doc and doc.count("<Play>") == 2


def test_alert_call_posts_to_twilio(monkeypatch):
    calls = {}

    class R:
        status_code = 201

        def json(self):
            return {"sid": "CA123456"}

    def fake_post(url, auth, data, timeout):
        calls.update(url=url, auth=auth, data=data)
        return R()

    secrets = {"twilio-sid": "AC1", "twilio-token": "tok", "twilio-from": "+15550001111"}
    monkeypatch.setattr(config, "param", lambda n: secrets[n])
    monkeypatch.setattr(voicecall, "speech_mp3", lambda text: b"mp3")
    monkeypatch.setattr(voicecall, "audio_url", lambda mp3: "https://x/a.mp3")
    monkeypatch.setattr(voicecall.requests, "post", fake_post)
    assert voicecall.alert_call("9876543210", {"text": "Dhyan dein"}) == "CA123456"
    assert calls["url"].endswith("/Accounts/AC1/Calls.json") and calls["data"]["To"] == "+919876543210"
    assert "<Play>https://x/a.mp3</Play>" in calls["data"]["Twiml"]


def test_unverified_number_is_permanent(monkeypatch):
    from ihcommon.channel import PermanentError

    class R:
        status_code, content, text = 400, b"x", '{"code":21219}'

        def json(self):
            return {"code": 21219}

    monkeypatch.setattr(config, "param", lambda n: "x")
    monkeypatch.setattr(voicecall.requests, "post", lambda *a, **k: R())
    with pytest.raises(PermanentError):
        voicecall.place_call("+14155550100", "<Response/>")
