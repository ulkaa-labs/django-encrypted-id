"""AES-SIV 64-bit ekey tests."""

import uuid

import pytest
from django.test import override_settings

from encrypted_id import (
    EncryptedIDDecodeError,
    decode_ekey,
    encode_ekey,
)


def test_ekey_roundtrip():
    sub_key = uuid.uuid4().hex
    assert decode_ekey(encode_ekey(10, sub_key), sub_key) == 10
    assert decode_ekey(encode_ekey(0, sub_key), sub_key) == 0
    assert decode_ekey(encode_ekey(2**64 - 1, sub_key), sub_key) == 2**64 - 1


def test_ekey_length_and_charset():
    token = encode_ekey(12345, "orders")
    assert len(token) == 32
    assert set(token) <= set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    )


def test_ekey_deterministic():
    sub_key = "same"
    assert encode_ekey(99, sub_key) == encode_ekey(99, sub_key)


def test_ekey_sub_key_isolates():
    a = encode_ekey(1, "table-a")
    b = encode_ekey(1, "table-b")
    assert a != b
    with pytest.raises(EncryptedIDDecodeError):
        decode_ekey(a, "table-b")


def test_ekey_rejects_invalid_id():
    with pytest.raises(ValueError):
        encode_ekey(-1, "s")
    with pytest.raises(ValueError):
        encode_ekey(2**64, "s")
    with pytest.raises(TypeError):
        encode_ekey(True, "s")


def test_ekey_tamper_detected():
    token = encode_ekey(7, "sub")
    tweaked = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(EncryptedIDDecodeError):
        decode_ekey(tweaked, "sub")


@override_settings(
    SECRET_KEY="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    SECRET_KEYS=[
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    ],
)
def test_ekey_secret_rotation():
    with override_settings(SECRET_KEY="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"):
        token = encode_ekey(7, "sub")
    with override_settings(SECRET_KEY="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"):
        assert decode_ekey(token, "sub") == 7
