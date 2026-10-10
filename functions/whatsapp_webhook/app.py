"""WhatsApp Cloud API webhook (API Gateway -> Lambda). Same bot logic as Telegram.

GET  /whatsapp  Meta's verification handshake (hub.verify_token)
POST /whatsapp  messages; X-Hub-Signature-256 must match HMAC-SHA256(app secret, raw body)
Incoming messages are translated into the update shape ihcommon.bot already handles,
with chat ids "wa:<number>".
"""

import base64
import hashlib
import hmac
import json

import boto3

from ihcommon import bot, config, repo
from ihcommon.log import log, metric
from ihcommon.whatsapp import PREFIX, WhatsApp


class Deps:
    def __init__(self):
        self.t = repo.table()
        self.bot = WhatsApp(config.param("whatsapp-token"), config.param("whatsapp-phone-id"))
        self.key = config.param("data-key")
        self.sfn = boto3.client("stepfunctions", region_name=config.REGION)
        self.lam = boto3.client("lambda", region_name=config.REGION)


_deps: Deps | None = None


def deps() -> Deps:
    global _deps
    if _deps is None:
        _deps = Deps()
    return _deps


def resp(code: int, body: str = "ok") -> dict:
    return {"statusCode": code, "headers": {"content-type": "text/plain"}, "body": body}


def raw_body(event: dict) -> bytes:
    body = event.get("body") or ""
    return base64.b64decode(body) if event.get("isBase64Encoded") else body.encode()


def signature_ok(body: bytes, header: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(header or "", expected)


def to_updates(payload: dict) -> list[dict]:
    """WhatsApp webhook payload -> Telegram-shaped updates for ihcommon.bot."""
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in change.get("value", {}).get("messages", []) or []:
                chat = {"id": PREFIX + m["from"]}
                kind = m.get("type")
                if kind == "text":
                    out.append({"message": {"chat": chat, "text": m["text"]["body"]}})
                elif kind == "interactive" and m["interactive"].get("type") == "button_reply":
                    out.append({"callback_query": {"id": m["id"], "data": m["interactive"]["button_reply"]["id"],
                                                   "message": {"chat": chat}}})
                elif kind == "button":  # quick-reply on a template message
                    out.append({"callback_query": {"id": m["id"], "data": m["button"].get("payload", ""),
                                                   "message": {"chat": chat}}})
                elif kind == "audio":
                    out.append({"message": {"chat": chat, "voice": {"file_id": m["audio"]["id"]}}})
    return out


def handler(event, _ctx):
    config.learn_base_url(event)
    method = event.get("requestContext", {}).get("http", {}).get("method", "POST")
    try:
        if method == "GET":
            q = event.get("queryStringParameters") or {}
            if q.get("hub.mode") == "subscribe" and hmac.compare_digest(
                    q.get("hub.verify_token", ""), config.param("whatsapp-verify-token")):
                return resp(200, q.get("hub.challenge", ""))
            return resp(403, "forbidden")
        secret = config.param("whatsapp-app-secret")
    except Exception as e:  # secrets not set up yet: fail closed
        log("whatsapp_secret_unavailable", error=type(e).__name__)
        return resp(401, "unauthorized")

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    body = raw_body(event)
    if not signature_ok(body, headers.get("x-hub-signature-256", ""), secret):
        metric("WebhookRejected", channel="whatsapp")
        return resp(401, "unauthorized")
    d = deps()
    for update in to_updates(json.loads(body or b"{}")):
        try:
            if "callback_query" in update:
                bot.on_callback(d, update["callback_query"])
            else:
                bot.on_message(d, update["message"])
        except Exception as e:  # always 200 so Meta does not retry forever
            log("whatsapp_webhook_error", error=type(e).__name__, detail=str(e)[:300])
            metric("WebhookError", channel="whatsapp")
    return resp(200)
