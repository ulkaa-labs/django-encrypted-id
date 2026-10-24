import uuid

import pytest

from encrypted_id import encode, decode


def test_encode_roundtrip():
    sub_key = uuid.uuid4().hex
    assert decode(encode(10, sub_key), sub_key) == 10


def test_encode_rejects_invalid_id():
    with pytest.raises(ValueError):
        encode(-1, "sub")
    with pytest.raises(ValueError):
        encode(2**64, "sub")
    with pytest.raises(TypeError):
        encode(True, "sub")
    with pytest.raises(TypeError):
        encode("10", "sub")


def test_encode_large_id():
    sub_key = "table"
    the_id = 2**64 - 1
    assert decode(encode(the_id, sub_key), sub_key) == the_id
