"""32-bit base62 skey tests."""

import uuid

import pytest
from django.test import override_settings

from encrypted_id import (
    EncryptedIDDecodeError,
    decode_skey,
    encode_skey,
    skey,
)
from tapp.models import Foo


def test_skey_roundtrip():
    sub_key = uuid.uuid4().hex
    for the_id in (0, 1, 42, 2**32 - 1):
        token = encode_skey(the_id, sub_key)
        assert len(token) == 9
        assert decode_skey(token, sub_key) == the_id


def test_skey_length_always_nine():
    for the_id in range(0, 200, 17):
        assert len(encode_skey(the_id, "t")) == 9


def test_skey_charset_base62():
    token = encode_skey(999, "t")
    assert set(token) <= set(
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    )


def test_skey_deterministic():
    assert encode_skey(5, "x") == encode_skey(5, "x")


def test_skey_rejects_above_uint32():
    with pytest.raises(ValueError):
        encode_skey(2**32, "t")
    with pytest.raises(ValueError):
        encode_skey(-1, "t")


def test_skey_tamper_detected():
    token = encode_skey(8, "sub")
    chars = list(token)
    chars[3] = "A" if chars[3] != "A" else "B"
    with pytest.raises(EncryptedIDDecodeError):
        decode_skey("".join(chars), "sub")


def test_skey_invalid_length():
    with pytest.raises(EncryptedIDDecodeError):
        decode_skey("short", "sub")
    with pytest.raises(EncryptedIDDecodeError):
        decode_skey("toolongkey", "sub")


@override_settings(
    SECRET_KEY="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    SECRET_KEYS=[
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    ],
)
def test_skey_secret_rotation():
    with override_settings(SECRET_KEY="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"):
        token = encode_skey(7, "sub")
    with override_settings(SECRET_KEY="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"):
        assert decode_skey(token, "sub") == 7


def test_skey_model_helpers(db):
    foo = Foo.objects.create(text="skey")
    assert foo.skey == skey(foo)
    assert len(foo.skey) == 9
    assert foo == Foo.objects.get_by_skey(foo.skey)
    assert foo == Foo.objects.get(skey=foo.skey)
    assert foo == Foo.objects.filter(skey=foo.skey).get()
