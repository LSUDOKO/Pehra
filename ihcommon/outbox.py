"""Outgoing messages go through SQS; the sender Lambda drains it under Telegram's rate limits."""

import json

import boto3

from ihcommon import config


def enqueue(chat_enc: str, kind: str, *, text: str = "", buttons=None, voice_key: str = "",
            dedupe: str = "") -> None:
    """kind: 'text' or 'voice'. chat_enc is the encrypted chat id (decrypted only in the sender)."""
    body = {"chat_enc": chat_enc, "kind": kind, "text": text, "buttons": buttons or [],
            "voice_key": voice_key, "dedupe": dedupe}
    boto3.client("sqs", region_name=config.REGION).send_message(
        QueueUrl=config.OUT_QUEUE_URL, MessageBody=json.dumps(body))


def enqueue_call(site: dict, speech: str) -> bool:
    """Queue a Hindi voice call if the supervisor opted in (/call_on). Returns True if queued."""
    if not site.get("call_enc"):
        return False
    enqueue(site["call_enc"], "call", text=speech)
    return True
