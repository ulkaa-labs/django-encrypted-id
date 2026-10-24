import pytest
from django.http import Http404
from django.shortcuts import get_list_or_404, get_object_or_404

from tapp.models import Bar, Foo, Foo2


def test_model(db):
    foo = Foo.objects.create(text="hello")
    assert foo.ekey
    assert len(foo.ekey) == 32
    assert foo == Foo.objects.get_by_ekey(foo.ekey)
    assert foo == Foo.objects.get_by_ekey_or_404(foo.ekey)
    assert foo == Foo.objects.get(ekey=foo.ekey)
    assert foo == Foo.objects.filter(ekey=foo.ekey).get()

    foo = Foo2.objects.create(text="hello")
    assert foo.ekey
    assert foo == Foo2.objects.get_by_ekey(foo.ekey)
    assert foo == Foo2.objects.get_by_ekey_or_404(foo.ekey)
    assert foo == Foo2.objects.get(ekey=foo.ekey)
    assert foo == Foo2.objects.filter(ekey=foo.ekey).get()

    with pytest.raises(Http404):
        Foo.objects.get_by_ekey_or_404("123123")

    with pytest.raises(Http404):
        get_list_or_404(Foo, ekey="123123")

    with pytest.raises(Http404):
        get_object_or_404(Foo, ekey="123123")


def test_sub_key(db):
    foo = Foo.objects.create(text="hello")

    try:
        foo2 = Foo2.objects.get(pk=foo.pk)
    except Foo2.DoesNotExist:
        foo2 = Foo2.objects.create(pk=foo.pk, text="hello")

    try:
        bar = Bar.objects.get(pk=foo.pk)
    except Bar.DoesNotExist:
        bar = Bar.objects.create(pk=foo.pk, text="hello")

    assert foo.pk == foo2.pk == bar.pk
    assert foo.ekey == foo2.ekey
    assert foo.ekey != bar.ekey
    assert foo.skey == foo2.skey
    assert foo.skey != bar.skey


def test_unsaved_ekey_raises(db):
    foo = Foo(text="unsaved")
    with pytest.raises(ValueError):
        _ = foo.ekey
    with pytest.raises(ValueError):
        _ = foo.skey
