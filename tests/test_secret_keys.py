"""SECRET_KEYS rotation support."""

import pytest
from django.test import override_settings

from encrypted_id import EncryptedIDDecodeError, decode, encode


@override_settings(
    SECRET_KEY="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    SECRET_KEYS=[
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    ],
)
def test_decode_tries_all_secret_keys():
    # Encrypted under the older key (second in SECRET_KEYS / "current" for encode).
    with override_settings(SECRET_KEY="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"):
        token = encode(7, "sub")

    # After rotation, encode uses the new key but decode still accepts old tokens.
    with override_settings(SECRET_KEY="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"):
        assert decode(token, "sub") == 7
        assert decode(encode(7, "sub"), "sub") == 7


@override_settings(SECRET_KEY="cccccccccccccccccccccccccccccccc")
def test_decode_fails_with_wrong_secret():
    token = encode(3, "sub")
    with override_settings(SECRET_KEY="dddddddddddddddddddddddddddddddd"):
        with pytest.raises(EncryptedIDDecodeError):
            decode(token, "sub")
