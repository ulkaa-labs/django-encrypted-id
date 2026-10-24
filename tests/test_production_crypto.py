"""Deep crypto / property tests for production readiness."""

import random
import string
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.test import override_settings

from encrypted_id import (
    EncryptedIDDecodeError,
    decode,
    decode_ekey,
    decode_skey,
    encode,
    encode_ekey,
    encode_skey,
)


SUB = "prod-table"


@pytest.mark.parametrize("the_id", [0, 1, 2, 255, 256, 2**31 - 1, 2**32 - 1])
def test_skey_boundary_ids(the_id):
    token = encode_skey(the_id, SUB)
    assert len(token) == 9
    assert decode_skey(token, SUB) == the_id


@pytest.mark.parametrize(
    "the_id",
    [0, 1, 2**32, 2**63 - 1, 2**64 - 1],
)
def test_ekey_boundary_ids(the_id):
    token = encode_ekey(the_id, SUB)
    assert len(token) == 32
    assert decode_ekey(token, SUB) == the_id


def test_ekey_mass_roundtrip_unique():
    ids = list(range(500)) + [random.randrange(0, 2**63) for _ in range(500)]
    tokens = [encode_ekey(i, SUB) for i in ids]
    assert len(set(tokens)) == len(ids)
    for i, token in zip(ids, tokens):
        assert decode_ekey(token, SUB) == i
        assert len(token) == 32


def test_skey_mass_roundtrip_unique():
    ids = list(range(2000))
    tokens = [encode_skey(i, SUB) for i in ids]
    assert len(set(tokens)) == len(ids)
    for i, token in zip(ids, tokens):
        assert decode_skey(token, SUB) == i


def test_sequential_ids_are_not_sequential_tokens():
    """Tokens must not leak ordering of sequential primary keys."""
    ekeys = [encode_ekey(i, SUB) for i in range(1, 21)]
    skeys = [encode_skey(i, SUB) for i in range(1, 21)]
    assert ekeys != sorted(ekeys)
    assert skeys != sorted(skeys)
    # Adjacent ids must not share long common prefixes (CBC/ECB style leak).
    for a, b in zip(ekeys, ekeys[1:]):
        assert a[:8] != b[:8] or a[8:16] != b[8:16]


def test_ekey_bit_flip_always_rejected():
    token = encode_ekey(42, SUB)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    failures = 0
    for i in range(len(token)):
        for ch in alphabet:
            if ch == token[i]:
                continue
            tweaked = token[:i] + ch + token[i + 1:]
            try:
                decode_ekey(tweaked, SUB)
            except EncryptedIDDecodeError:
                failures += 1
            else:
                pytest.fail("forged ekey accepted at position %d" % i)
            break  # one flip per position is enough
    assert failures == len(token)


def test_skey_single_char_flip_usually_rejected():
    token = encode_skey(42, SUB)
    accepted = 0
    checked = 0
    for i in range(len(token)):
        for ch in string.ascii_letters + string.digits:
            if ch == token[i]:
                continue
            tweaked = token[:i] + ch + token[i + 1:]
            checked += 1
            try:
                decode_skey(tweaked, SUB)
                accepted += 1
            except EncryptedIDDecodeError:
                pass
            break
    # 16-bit MAC ⇒ forgery should almost always fail; allow zero accepts.
    assert accepted == 0
    assert checked == len(token)


def test_cross_format_tokens_do_not_decode():
    e = encode_ekey(9, SUB)
    s = encode_skey(9, SUB)
    legacy = encode(9, SUB)
    with pytest.raises(EncryptedIDDecodeError):
        decode_skey(e[:9], SUB)  # wrong payload even if length matches by chance
    with pytest.raises(EncryptedIDDecodeError):
        decode_ekey(s + s + s + "ABCD", SUB)
    with pytest.raises(EncryptedIDDecodeError):
        decode_ekey(legacy, SUB)  # legacy is 22 chars
    with pytest.raises(EncryptedIDDecodeError):
        decode(e, SUB)


def test_sub_key_and_secret_isolation():
    token = encode_ekey(100, "alpha")
    with pytest.raises(EncryptedIDDecodeError):
        decode_ekey(token, "beta")
    stoken = encode_skey(100, "alpha")
    with pytest.raises(EncryptedIDDecodeError):
        decode_skey(stoken, "beta")


@override_settings(SECRET_KEY="prod-secret-key-32-bytes-minimum!!")
def test_unicode_sub_key_roundtrip():
    sub = "订单-表"
    assert decode_ekey(encode_ekey(5, sub), sub) == 5
    assert decode_skey(encode_skey(5, sub), sub) == 5


def test_thread_safe_encode_decode():
    ids = list(range(100))

    def work(i):
        e = encode_ekey(i, SUB)
        s = encode_skey(i % (2**16), SUB)
        assert decode_ekey(e, SUB) == i
        assert decode_skey(s, SUB) == i % (2**16)
        return e, s

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(work, ids))
    assert len({r[0] for r in results}) == 100


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "x",
        "!" * 32,
        "a" * 31,
        "a" * 33,
        None,
        123,
        b"\xff\xfe",
        "emoji-😀-not-ascii!!!!!!!!!!",
    ],
)
def test_ekey_rejects_garbage(bad):
    with pytest.raises((EncryptedIDDecodeError, TypeError, AttributeError)):
        decode_ekey(bad, SUB)


@pytest.mark.parametrize(
    "bad",
    ["", "short", "toolong12", "bad!char1", None, 9, "---------"],
)
def test_skey_rejects_garbage(bad):
    with pytest.raises((EncryptedIDDecodeError, TypeError, AttributeError)):
        decode_skey(bad, SUB)
