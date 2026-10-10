"""Messaging channel interface. Telegram today; WhatsApp is a drop-in adapter later.

Buttons are (label, callback_data) rows.
"""

from typing import Protocol

Buttons = list[list[tuple[str, str]]]


class RateLimited(Exception):
    def __init__(self, retry_after: int):
        super().__init__(f"rate limited, retry after {retry_after}s")
        self.retry_after = retry_after


class PermanentError(Exception):
    """The provider will never accept this message (unverified or not-allowed number). Do not retry."""


class OutsideWindow(Exception):
    """WhatsApp: no customer-service window open (user has not messaged in 24 h); needs a paid template."""


class Channel(Protocol):
    def send_text(self, chat_id: str, text: str, buttons: Buttons | None = None) -> dict: ...

    def send_voice(self, chat_id: str, audio: bytes, caption: str = "") -> dict: ...

    def answer_button(self, callback_id: str, text: str = "") -> None: ...
