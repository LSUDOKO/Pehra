"""WhatsApp Cloud API client (Meta). Same Channel interface as Telegram.

Demo setup uses Meta's free test number: up to 5 verified recipients, no payment method.
Free-form text, audio and reply buttons need an open 24-hour customer service window
(the supervisor messaged us in the last 24 h). Scheduled pushes outside it need a paid
utility template, which this weekend build does not use.

Chat ids are "wa:<E.164 digits>" inside the app; the prefix is stripped here.
"""

import os

import requests

from ihcommon.channel import Buttons, RateLimited

GRAPH = "https://graph.facebook.com"
API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v23.0")
TIMEOUT_S = 15
MAX_BUTTONS = 3
MAX_BUTTON_TITLE = 20
MAX_INTERACTIVE_BODY = 1024
RATE_LIMIT_CODES = {130429, 131056, 80007}  # throughput, pair rate limit, account rate limit
PREFIX = "wa:"


def strip(chat_id: str) -> str:
    return chat_id[len(PREFIX):] if chat_id.startswith(PREFIX) else chat_id


class WhatsApp:
    def __init__(self, token: str, phone_number_id: str, session: requests.Session | None = None):
        self._token = token
        self._base = f"{GRAPH}/{API_VERSION}/{phone_number_id}"
        self._s = session or requests.Session()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def _check(self, r) -> dict:
        body = r.json() if r.content else {}
        if r.status_code >= 400 or "error" in body:
            err = body.get("error", {})
            if r.status_code == 429 or err.get("code") in RATE_LIMIT_CODES:
                raise RateLimited(6)
            raise RuntimeError(f"whatsapp failed: {r.status_code} {err.get('code')} {err.get('message', '')}")
        return body

    def _send(self, payload: dict) -> dict:
        r = self._s.post(f"{self._base}/messages", headers=self._headers(), timeout=TIMEOUT_S,
                         json={"messaging_product": "whatsapp", "recipient_type": "individual", **payload})
        return self._check(r)

    def send_text(self, chat_id: str, text: str, buttons: Buttons | None = None) -> dict:
        to = strip(chat_id)
        flat = [b for row in (buttons or []) for b in row][:MAX_BUTTONS]
        if not flat:
            return self._send({"to": to, "type": "text", "text": {"body": text[:4096]}})
        body = text
        if len(text) > MAX_INTERACTIVE_BODY:  # long plan: send it, then a short button prompt
            self._send({"to": to, "type": "text", "text": {"body": text[:4096]}})
            body = "Plan upar hai. Kya karna hai?"
        return self._send({"to": to, "type": "interactive", "interactive": {
            "type": "button", "body": {"text": body},
            "action": {"buttons": [{"type": "reply", "reply": {"id": data[:256], "title": label[:MAX_BUTTON_TITLE]}}
                                   for label, data in flat]}}})

    def upload_media(self, data: bytes, mime: str, filename: str) -> str:
        r = self._s.post(f"{self._base}/media", headers=self._headers(), timeout=TIMEOUT_S,
                         data={"messaging_product": "whatsapp", "type": mime},
                         files={"file": (filename, data, mime)})
        return self._check(r)["id"]

    def send_voice(self, chat_id: str, audio: bytes, caption: str = "") -> dict:
        """OGG/Opus from Polly; WhatsApp plays it as an audio message."""
        media_id = self.upload_media(audio, "audio/ogg", "plan.ogg")
        return self._send({"to": strip(chat_id), "type": "audio", "audio": {"id": media_id}})

    def answer_button(self, callback_id: str, text: str = "") -> None:
        """WhatsApp has no callback acknowledgement; mark the button message as read instead."""
        try:
            self._send({"status": "read", "message_id": callback_id})
        except Exception:
            pass

    def download_file(self, media_id: str) -> bytes:
        meta = self._check(self._s.get(f"{GRAPH}/{API_VERSION}/{media_id}", headers=self._headers(),
                                       timeout=TIMEOUT_S))
        r = self._s.get(meta["url"], headers=self._headers(), timeout=TIMEOUT_S)
        r.raise_for_status()
        return r.content
