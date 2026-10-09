"""Privacy helpers: keyed hashes for lookups, AES-GCM for the one reversible chat id.

The key lives in SSM (`/invisible-heat/data-key`, 32 random bytes, base64).
"""

import base64
import hashlib
import hmac
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _key(key_b64: str) -> bytes:
    k = base64.b64decode(key_b64)
    if len(k) != 32:
        raise ValueError("data key must be 32 bytes")
    return k


def keyed_hash(value: str, key_b64: str) -> str:
    """HMAC-SHA256, hex. Used as the DynamoDB key for chat ids and device tokens."""
    return hmac.new(_key(key_b64), str(value).encode(), hashlib.sha256).hexdigest()


def encrypt(plaintext: str, key_b64: str) -> str:
    nonce = os.urandom(12)
    ct = AESGCM(_key(key_b64)).encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ct).decode()


def decrypt(token: str, key_b64: str) -> str:
    raw = base64.urlsafe_b64decode(token)
    return AESGCM(_key(key_b64)).decrypt(raw[:12], raw[12:], None).decode()


def new_site_token() -> str:
    """128-bit random, URL-safe; printed in the site's QR code."""
    return secrets.token_urlsafe(16)
