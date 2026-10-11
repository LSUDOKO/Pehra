"""Drains the outgoing queue into Telegram. Reserved concurrency 1 keeps us under rate limits.

On 429 the message is returned to the queue (partial batch failure) and retried later;
after repeated failures SQS moves it to the dead-letter queue.
"""

import json
import os
import time

import boto3

from ihcommon import channels, config
from ihcommon.channel import OutsideWindow, PermanentError, RateLimited
from ihcommon.crypto import decrypt
from ihcommon.log import log, metric

MIN_GAP_S = 0.05        # ~20 msgs/s overall, below Telegram's ~30/s bot limit
WHATSAPP_PAIR_GAP_S = 6
TEST_PREFIX = "test:"  # WhatsApp: about one message per 6 s to the same user


def deliver(msg: dict, s3=None) -> str:
    chat_id = decrypt(msg["chat_enc"], config.param("data-key"))
    if chat_id.startswith(TEST_PREFIX):  # smoke tests: never contact anyone
        log("smoke_message_dropped", kind=msg["kind"], chars=len(msg.get("text", "")))
        return chat_id
    if msg["kind"] == "call":
        from ihcommon import voicecall
        voicecall.alert_call(chat_id, msg)
        return chat_id
    bot = channels.client_for(chat_id)
    if msg["kind"] == "voice":
        s3 = s3 or boto3.client("s3", region_name=config.REGION)
        audio = s3.get_object(Bucket=config.MEDIA_BUCKET, Key=msg["voice_key"])["Body"].read()
        bot.send_voice(chat_id, audio)
    else:
        buttons = [[tuple(b) for b in row] for row in msg.get("buttons") or []]
        bot.send_text(chat_id, msg["text"], buttons or None)
    return chat_id


REOPEN_TEMPLATE = os.environ.get("WHATSAPP_REOPEN_TEMPLATE", "hello_world")
REOPEN_LANG = os.environ.get("WHATSAPP_REOPEN_LANG", "en_US")
REOPEN_EVERY_S = 12 * 3600


def hold_and_nudge(msg: dict) -> None:
    from ihcommon import repo
    from ihcommon.crypto import keyed_hash

    key = config.param("data-key")
    chat_id = decrypt(msg["chat_enc"], key)
    owner = keyed_hash(chat_id, key)
    t = repo.table()
    repo.add_pending(t, owner, msg)
    metric("WhatsAppHeldForWindow")
    if repo.claim_once(t, f"reopen#{owner}", REOPEN_EVERY_S):
        try:
            channels.client_for(chat_id).send_template(chat_id, REOPEN_TEMPLATE, REOPEN_LANG)
            metric("WhatsAppReopenTemplateSent")
        except Exception as e:
            log("reopen_template_failed", error=type(e).__name__, detail=str(e)[:200])


def handler(event, _ctx):
    failures, last_sent = [], {}
    for rec in event.get("Records", []):
        try:
            msg = json.loads(rec["body"])
            key = msg["chat_enc"]
            wait = last_sent.get(key, 0) + WHATSAPP_PAIR_GAP_S - time.time()
            if key in last_sent and wait > 0 and channels.is_whatsapp(
                    decrypt(key, config.param("data-key"))):
                time.sleep(wait)
            deliver(msg)
            last_sent[key] = time.time()
            metric("MessageSent", kind=msg["kind"])
            time.sleep(MIN_GAP_S)
        except OutsideWindow:
            # WhatsApp 24 h rule: hold the message, nudge with an approved template, deliver on reply.
            hold_and_nudge(msg)
        except PermanentError as e:
            log("send_permanent_failure", detail=str(e)[:200])
            metric("MessagePermanentFailure")
        except RateLimited as e:
            log("telegram_rate_limited", retry_after=e.retry_after)
            failures.append({"itemIdentifier": rec["messageId"]})
        except Exception as e:
            log("send_failed", error=type(e).__name__, detail=str(e)[:200])
            metric("MessageFailed")
            failures.append({"itemIdentifier": rec["messageId"]})
    return {"batchItemFailures": failures}
