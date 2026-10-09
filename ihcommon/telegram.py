"""Telegram Bot API client (free, no approval, voice notes and inline buttons)."""

import requests

from ihcommon.channel import Buttons, RateLimited

API = "https://api.telegram.org"
TIMEOUT_S = 15


class Telegram:
    def __init__(self, token: str, session: requests.Session | None = None):
        self._base = f"{API}/bot{token}"
        self._file_base = f"{API}/file/bot{token}"
        self._s = session or requests.Session()

    def _call(self, method: str, data: dict | None = None, files: dict | None = None) -> dict:
        r = self._s.post(f"{self._base}/{method}", json=None if files else data,
                         data=data if files else None, files=files, timeout=TIMEOUT_S)
        body = r.json() if r.content else {}
        if r.status_code == 429:
            raise RateLimited(int(body.get("parameters", {}).get("retry_after", 5)))
        if not body.get("ok"):
            raise RuntimeError(f"telegram {method} failed: {r.status_code} "
                               f"{body.get('description', '')}")
        return body["result"]

    @staticmethod
    def keyboard(buttons: Buttons) -> dict:
        return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row]
                                    for row in buttons]}

    def send_text(self, chat_id: str, text: str, buttons: Buttons | None = None) -> dict:
        data = {"chat_id": chat_id, "text": text}
        if buttons:
            data["reply_markup"] = self.keyboard(buttons)
        return self._call("sendMessage", data)

    def send_voice(self, chat_id: str, audio: bytes, caption: str = "") -> dict:
        """OGG/Opus bytes play as a voice note in Telegram."""
        return self._call("sendVoice", {"chat_id": chat_id, "caption": caption},
                          files={"voice": ("plan.ogg", audio, "audio/ogg")})

    def answer_button(self, callback_id: str, text: str = "") -> None:
        self._call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})

    def clear_buttons(self, chat_id: str, message_id: int) -> None:
        self._call("editMessageReplyMarkup", {"chat_id": chat_id, "message_id": message_id,
                                              "reply_markup": {"inline_keyboard": []}})

    def download_file(self, file_id: str) -> bytes:
        path = self._call("getFile", {"file_id": file_id})["file_path"]
        r = self._s.get(f"{self._file_base}/{path}", timeout=TIMEOUT_S)
        r.raise_for_status()
        return r.content

    def set_webhook(self, url: str, secret: str) -> dict:
        return self._call("setWebhook", {"url": url, "secret_token": secret,
                                         "allowed_updates": ["message", "callback_query"]})
