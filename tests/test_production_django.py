"""Deep Django integration tests for production readiness."""

import pytest
from django.http import Http404
from django.test import Client
from django.urls import reverse

from encrypted_id import (
    EncryptedIDDecodeError,
    ekey,
    get_object_or_404,
    get_object_or_404_skey,
    skey,
)
from tapp.models import Bar, BigItem, Foo, Foo2


@pytest.fixture
def samples(db):
    return [
        Foo.objects.create(text="a"),
        Foo.objects.create(text="b"),
        Foo.objects.create(text="c"),
    ]


def test_detail_view_ekey_and_skey(samples):
    client = Client()
    foo = samples[0]

    r = client.get(reverse("foo", args=(foo.ekey,)))
    assert r.status_code == 200
    assert r.context["object"] == foo

    r = client.get(reverse("foo_skey", args=(foo.skey,)))
    assert r.status_code == 200
    assert r.context["object"] == foo

    r = client.get(reverse("foo_ekey_func", args=(foo.ekey,)))
    assert r.status_code == 200
    assert r.content.decode() == str(foo.pk)

    r = client.get(reverse("foo_skey_func", args=(foo.skey,)))
    assert r.status_code == 200
    assert r.content.decode() == str(foo.pk)


def test_views_404_on_forged_tokens(samples):
    client = Client()
    bad_ekey = "A" * 32
    bad_skey = "000000000"
    assert client.get(reverse("foo", args=(bad_ekey,))).status_code == 404
    assert client.get(reverse("foo_skey", args=(bad_skey,))).status_code == 404
    assert client.get(reverse("foo_ekey_func", args=(bad_ekey,))).status_code == 404
    assert client.get(reverse("foo_skey_func", args=(bad_skey,))).status_code == 404


def test_manager_extra_filters(samples):
    foo = samples[1]
    assert Foo.objects.get_by_ekey(foo.ekey, text="b") == foo
    with pytest.raises(Foo.DoesNotExist):
        Foo.objects.get_by_ekey(foo.ekey, text="nope")

    assert Foo.objects.get_by_skey(foo.skey, text="b") == foo
    with pytest.raises(Foo.DoesNotExist):
        Foo.objects.get_by_skey(foo.skey, text="nope")


def test_queryset_filter_and_exclude(samples):
    foo, other, _ = samples
    assert Foo.objects.filter(ekey=foo.ekey).get() == foo
    assert Foo.objects.filter(skey=foo.skey).get() == foo
    assert Foo.objects.filter(ekey=foo.ekey, text=foo.text).get() == foo

    qs = Foo.objects.exclude(ekey=foo.ekey)
    assert foo not in qs
    assert other in qs

    qs = Foo.objects.exclude(skey=foo.skey)
    assert foo not in qs
    assert other in qs

    # Invalid token exclude is a no-op (matches nothing to exclude).
    assert Foo.objects.exclude(ekey="not-a-valid-ekey-token!!!!").count() == 3
    assert Foo.objects.filter(ekey="not-a-valid-ekey-token!!!!").count() == 0


def test_conflicting_ekey_and_skey_returns_empty(samples):
    a, b, _ = samples
    assert Foo.objects.filter(ekey=a.ekey, skey=b.skey).count() == 0
    assert Foo.objects.filter(ekey=a.ekey, skey=a.skey).get() == a


def test_get_object_or_404_with_extra_kwargs(samples):
    foo = samples[0]
    assert get_object_or_404(Foo, foo.ekey, text=foo.text) == foo
    with pytest.raises(Http404):
        get_object_or_404(Foo, foo.ekey, text="missing")
    assert get_object_or_404_skey(Foo, foo.skey, text=foo.text) == foo
    with pytest.raises(Http404):
        get_object_or_404_skey(Foo, foo.skey, text="missing")


def test_helpers_match_model_properties(samples):
    foo = samples[0]
    assert ekey(foo) == foo.ekey
    assert skey(foo) == foo.skey


def test_ek_key_meta_shared_between_models(db):
    foo = Foo.objects.create(text="x")
    foo2 = Foo2.objects.create(pk=foo.pk, text="x")
    bar = Bar.objects.create(pk=foo.pk, text="x")
    assert foo.ekey == foo2.ekey
    assert foo.skey == foo2.skey
    assert foo.ekey != bar.ekey
    assert foo.skey != bar.skey


def test_bigautofield_ekey_works(db):
    item = BigItem.objects.create(text="big")
    assert len(item.ekey) == 32
    assert BigItem.objects.get_by_ekey(item.ekey) == item


def test_bigautofield_skey_ok_for_small_pk(db):
    item = BigItem.objects.create(text="small")
    assert item.pk < 2**32
    assert len(item.skey) == 9
    assert BigItem.objects.get_by_skey(item.skey) == item


def test_bigautofield_skey_rejects_large_pk(db):
    item = BigItem(text="huge")
    item.pk = 2**32
    with pytest.raises(ValueError, match="skey requires pk"):
        _ = item.skey
    # ekey still works for large ids
    assert len(item.ekey) == 32


def test_invalid_get_by_ekey_raises_decode_error(samples):
    with pytest.raises(EncryptedIDDecodeError):
        Foo.objects.get_by_ekey("totally-invalid-token-xxxxxx")


def test_chained_queryset_still_supports_ekey(samples):
    foo = samples[0]
    qs = Foo.objects.filter(text=foo.text).filter(ekey=foo.ekey)
    assert qs.get() == foo
    qs = Foo.objects.all().exclude(text="nope").filter(skey=foo.skey)
    assert qs.get() == foo


def test_many_objects_unique_tokens(db):
    objs = [Foo.objects.create(text=str(i)) for i in range(50)]
    ekeys = [o.ekey for o in objs]
    skeys = [o.skey for o in objs]
    assert len(set(ekeys)) == 50
    assert len(set(skeys)) == 50
    for o in objs:
        assert Foo.objects.get(ekey=o.ekey) == o
        assert Foo.objects.get(skey=o.skey) == o
