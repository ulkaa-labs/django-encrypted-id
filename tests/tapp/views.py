from django.http import HttpResponse
from django.views.generic import DetailView

from encrypted_id import get_object_or_404, get_object_or_404_skey
from tapp.models import Foo


class FooView(DetailView):
    model = Foo
    slug_field = "ekey"
    template_name = "admin/base.html"


class FooSkeyView(DetailView):
    model = Foo
    slug_field = "skey"
    template_name = "admin/base.html"


def foo_ekey_func(request, token):
    obj = get_object_or_404(Foo, token)
    return HttpResponse(str(obj.pk))


def foo_skey_func(request, token):
    obj = get_object_or_404_skey(Foo, token)
    return HttpResponse(str(obj.pk))
