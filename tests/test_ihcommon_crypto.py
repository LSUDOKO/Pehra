import base64
import os

import pytest

from ihcommon.crypto import decrypt, encrypt, keyed_hash, new_site_token

KEY = base64.b64encode(os.urandom(32)).decode()


def test_roundtrip_and_nonce():
    a, b = encrypt("123456789", KEY), encrypt("123456789", KEY)
    assert a != b and decrypt(a, KEY) == "123456789"


def test_keyed_hash_stable_and_keyed():
    other = base64.b64encode(os.urandom(32)).decode()
    assert keyed_hash("42", KEY) == keyed_hash("42", KEY) != keyed_hash("42", other)


def test_bad_key():
    with pytest.raises(ValueError):
        keyed_hash("x", base64.b64encode(b"short").decode())


def test_site_token_entropy():
    assert len(new_site_token()) >= 21
