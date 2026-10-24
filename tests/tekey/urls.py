"""URL configuration for the encrypted_id test project."""

from django.contrib import admin
from django.urls import path, re_path

from tapp.views import FooSkeyView, FooView, foo_ekey_func, foo_skey_func

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(
        r"^foo/(?P<slug>[0-9A-Za-z_-]{32})/$",
        FooView.as_view(),
        name="foo",
    ),
    re_path(
        r"^s/(?P<slug>[0-9A-Za-z]{9})/$",
        FooSkeyView.as_view(),
        name="foo_skey",
    ),
    re_path(
        r"^fe/(?P<token>[0-9A-Za-z_-]{32})/$",
        foo_ekey_func,
        name="foo_ekey_func",
    ),
    re_path(
        r"^fs/(?P<token>[0-9A-Za-z]{9})/$",
        foo_skey_func,
        name="foo_skey_func",
    ),
]
