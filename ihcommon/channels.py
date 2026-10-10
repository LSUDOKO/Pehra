"""Pick the messaging client from a channel-qualified chat id ("wa:..." = WhatsApp)."""

import functools

from ihcommon import config
from ihcommon.whatsapp import PREFIX


def is_whatsapp(chat_id: str) -> bool:
    return chat_id.startswith(PREFIX)


@functools.cache
def _telegram():
    from ihcommon.telegram import Telegram
    return Telegram(config.param("telegram-token"))


@functools.cache
def _whatsapp():
    from ihcommon.whatsapp import WhatsApp
    return WhatsApp(config.param("whatsapp-token"), config.param("whatsapp-phone-id"))


def client_for(chat_id: str):
    return _whatsapp() if is_whatsapp(chat_id) else _telegram()
