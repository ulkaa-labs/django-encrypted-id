import pytest

from encrypted_id import EncryptedIDDecodeError, decode, encode


def test_decode_invalid_input():
    with pytest.raises(EncryptedIDDecodeError):
        decode("", "")
    with pytest.raises(EncryptedIDDecodeError):
        decode("1", "")
    with pytest.raises(EncryptedIDDecodeError):
        decode(encode(0, "")[:-1] + "Z", "")
    with pytest.raises(EncryptedIDDecodeError):
        decode(None, "")
    with pytest.raises(EncryptedIDDecodeError):
        decode("not-ascii-\u2603", "")


def test_decode_accepts_bytes():
    sub_key = "sub"
    ekey = encode(42, sub_key)
    assert decode(ekey.encode("ascii"), sub_key) == 42
