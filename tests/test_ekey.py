import pytest
from django.http import Http404

from encrypted_id import ekey, get_object_or_404, get_object_or_404_skey, skey
from tapp.models import Foo


def test_ekey(db):
    foo = Foo.objects.create(text="asd")
    assert ekey(foo) == foo.ekey
    assert len(foo.ekey) == 32
    assert foo == get_object_or_404(Foo, foo.ekey)


def test_skey_helper(db):
    foo = Foo.objects.create(text="asd")
    assert skey(foo) == foo.skey
    assert foo == get_object_or_404_skey(Foo, foo.skey)


def test_allow_none_ekey(db):
    with pytest.raises(Http404):
        get_object_or_404(Foo, None)

    with pytest.raises(Foo.DoesNotExist):
        Foo.objects.get(ekey=None)

    with pytest.raises(Http404):
        get_object_or_404_skey(Foo, None)

    with pytest.raises(Foo.DoesNotExist):
        Foo.objects.get(skey=None)
