"""Drains the outgoing queue into Telegram. Reserved concurrency 1 keeps us under rate limits.

On 429 the message is returned to the queue (partial batch failure) and retried later;
after repeated failures SQS moves it to the dead-letter queue.
"""

import json
import time

import boto3

from ihcommon import config
from ihcommon.channel import RateLimited
from ihcommon.crypto import decrypt
from ihcommon.log import log, metric
from ihcommon.telegram import Telegram

MIN_GAP_S = 0.05  # ~20 msgs/s overall, below Telegram's ~30/s bot limit


def _bot() -> Telegram:
    return Telegram(config.param("telegram-token"))


def deliver(bot, msg: dict, s3=None) -> None:
    chat_id = decrypt(msg["chat_enc"], config.param("data-key"))
    if msg["kind"] == "voice":
        s3 = s3 or boto3.client("s3", region_name=config.REGION)
        audio = s3.get_object(Bucket=config.MEDIA_BUCKET, Key=msg["voice_key"])["Body"].read()
        bot.send_voice(chat_id, audio)
    else:
        buttons = [[tuple(b) for b in row] for row in msg.get("buttons") or []]
        bot.send_text(chat_id, msg["text"], buttons or None)


def handler(event, _ctx):
    bot, failures = _bot(), []
    for rec in event.get("Records", []):
        try:
            deliver(bot, json.loads(rec["body"]))
            metric("MessageSent")
            time.sleep(MIN_GAP_S)
        except RateLimited as e:
            log("telegram_rate_limited", retry_after=e.retry_after)
            failures.append({"itemIdentifier": rec["messageId"]})
        except Exception as e:
            log("send_failed", error=type(e).__name__, detail=str(e)[:200])
            metric("MessageFailed")
            failures.append({"itemIdentifier": rec["messageId"]})
    return {"batchItemFailures": failures}
