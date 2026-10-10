"""Telegram webhook (API Gateway -> Lambda).

Fast paths are handled here; questions and voice notes go to the async assistant Lambda
so the webhook always answers Telegram quickly. Shared logic lives in ihcommon.bot.
"""

import hmac
import json

import boto3

from ihcommon import bot, config, repo
from ihcommon.log import log, metric, short_hash
from ihcommon.telegram import Telegram


class Deps:
    """Swappable for tests."""

    def __init__(self):
        self.t = repo.table()
        self.bot = Telegram(config.param("telegram-token"))
        self.key = config.param("data-key")
        self.sfn = boto3.client("stepfunctions", region_name=config.REGION)
        self.lam = boto3.client("lambda", region_name=config.REGION)


_deps: Deps | None = None


def deps() -> Deps:
    global _deps
    if _deps is None:
        _deps = Deps()
    return _deps


def ok(body: str = "ok") -> dict:
    return {"statusCode": 200, "body": body}


def handler(event, _ctx):
    config.learn_base_url(event)
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    try:
        expected = config.param("webhook-secret")
    except Exception as e:  # secrets not set up yet: fail closed
        log("webhook_secret_unavailable", error=type(e).__name__)
        return {"statusCode": 401, "body": "unauthorized"}
    if not hmac.compare_digest(headers.get("x-telegram-bot-api-secret-token", ""), expected):
        metric("WebhookRejected")
        return {"statusCode": 401, "body": "unauthorized"}
    update = json.loads(event.get("body") or "{}")
    d = deps()
    try:
        if "callback_query" in update:
            bot.on_callback(d, update["callback_query"])
        elif "message" in update:
            bot.on_message(d, update["message"])
    except Exception as e:  # never make Telegram retry forever
        log("webhook_error", error=type(e).__name__, detail=str(e)[:300],
            chat=short_hash(json.dumps(update)[:50]))
        metric("WebhookError")
    return ok()
