"""Hindi voice-call alerts through Twilio (demo: free trial account).

Twilio trial accounts can call only numbers verified in the Twilio console (up to 5), and
play a short trial notice first. The spoken text is fixed Hindi (never generated), voiced by
Polly as MP3, served from S3 via a short-lived presigned URL and played twice.
"""

import re
import uuid
from xml.sax.saxutils import escape

import boto3
import requests

from ihcommon import config
from ihcommon.log import log, metric, short_hash

TWILIO_API = "https://api.twilio.com/2010-04-01"
E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
URL_TTL_S = 900


def normalise_phone(raw: str) -> str | None:
    """'+91 98765-43210', '919876543210', 'wa:919876543210', '09876543210' -> '+919876543210'."""
    digits = re.sub(r"\D", "", raw.removeprefix("wa:"))
    if len(digits) == 11 and digits.startswith("0"):
        digits = "91" + digits[1:]
    if len(digits) == 10:
        digits = "91" + digits
    phone = "+" + digits
    return phone if E164_RE.match(phone) else None


def twiml(audio_url: str) -> str:
    u = escape(audio_url)
    return f'<Response><Play>{u}</Play><Pause length="1"/><Play>{u}</Play></Response>'


def speech_mp3(text: str) -> bytes:
    polly = boto3.client("polly", region_name=config.REGION)
    return polly.synthesize_speech(Text=text, VoiceId="Kajal", LanguageCode="hi-IN", Engine="neural",
                                   OutputFormat="mp3")["AudioStream"].read()


def audio_url(mp3: bytes) -> str:
    s3 = boto3.client("s3", region_name=config.REGION)
    key = f"calls/{uuid.uuid4().hex}.mp3"
    s3.put_object(Bucket=config.MEDIA_BUCKET, Key=key, Body=mp3, ContentType="audio/mpeg")
    return s3.generate_presigned_url("get_object", Params={"Bucket": config.MEDIA_BUCKET, "Key": key},
                                     ExpiresIn=URL_TTL_S)


def place_call(to: str, twiml_doc: str, session: requests.Session | None = None) -> str:
    sid, token = config.param("twilio-sid"), config.param("twilio-token")
    r = (session or requests).post(f"{TWILIO_API}/Accounts/{sid}/Calls.json", auth=(sid, token), timeout=15,
                                   data={"To": to, "From": config.param("twilio-from"), "Twiml": twiml_doc})
    if r.status_code >= 400:
        raise RuntimeError(f"twilio call failed: {r.status_code} {r.text[:200]}")
    return r.json()["sid"]


def alert_call(phone_raw: str, msg: dict) -> str:
    to = normalise_phone(phone_raw)
    if not to:
        raise ValueError("not a valid phone number")
    call_sid = place_call(to, twiml(audio_url(speech_mp3(msg["text"]))))
    metric("VoiceCallPlaced")
    log("voice_call", to=short_hash(to), call=call_sid[-6:])
    return call_sid
