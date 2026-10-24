"""Settings / rotation / configuration edge cases."""

import pytest
from django.test import override_settings

from encrypted_id import (
    EncryptedIDDecodeError,
    decode_ekey,
    decode_skey,
    encode_ekey,
    encode_skey,
)
from tapp.models import Foo


@override_settings(
    SECRET_KEY="current-secret-key-value-32b!!!!",
    SECRET_KEYS=[
        "current-secret-key-value-32b!!!!",
        "older-secret-key-value-32bytes!!",
        "oldest-secret-key-value-32byte!",
    ],
)
def test_rotation_reads_all_generations(db):
    tokens = {}
    for secret in (
        "oldest-secret-key-value-32byte!",
        "older-secret-key-value-32bytes!!",
        "current-secret-key-value-32b!!!!",
    ):
        with override_settings(SECRET_KEY=secret):
            tokens[secret] = (
                encode_ekey(11, "t"),
                encode_skey(11, "t"),
            )

    # With full SECRET_KEYS list, every generation decrypts.
    for e, s in tokens.values():
        assert decode_ekey(e, "t") == 11
        assert decode_skey(s, "t") == 11


@override_settings(SECRET_KEY="only-one-secret-key-32-bytes-ok!")
def test_without_secret_keys_setting():
    e = encode_ekey(3, "t")
    s = encode_skey(3, "t")
    assert decode_ekey(e, "t") == 3
    assert decode_skey(s, "t") == 3


@override_settings(
    SECRET_KEY="new-secret-key-________________",
    SECRET_KEYS=["new-secret-key-________________"],
)
def test_old_token_rejected_after_keys_dropped():
    with override_settings(SECRET_KEY="old-secret-key-_________________"):
        e = encode_ekey(4, "t")
        s = encode_skey(4, "t")
    with pytest.raises(EncryptedIDDecodeError):
        decode_ekey(e, "t")
    with pytest.raises(EncryptedIDDecodeError):
        decode_skey(s, "t")


@override_settings(SECRET_KEY="model-rotation-secret-32bytes!!")
def test_model_lookups_survive_listed_old_secret(db):
    with override_settings(SECRET_KEY="model-old-secret-key-32bytes!!!!"):
        foo = Foo.objects.create(text="rot")
        old_ekey = foo.ekey
        old_skey = foo.skey

    with override_settings(
        SECRET_KEY="model-rotation-secret-32bytes!!",
        SECRET_KEYS=[
            "model-rotation-secret-32bytes!!",
            "model-old-secret-key-32bytes!!!!",
        ],
    ):
        assert Foo.objects.get_by_ekey(old_ekey).pk == foo.pk
        assert Foo.objects.get_by_skey(old_skey).pk == foo.pk
        # Newly minted tokens use the current secret.
        foo_fresh = Foo.objects.get(pk=foo.pk)
        assert Foo.objects.get_by_ekey(foo_fresh.ekey) == foo_fresh
