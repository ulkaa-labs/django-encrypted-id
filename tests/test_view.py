from django.test import Client
from django.urls import reverse

from tapp.models import Foo


def test_view(db):
    client = Client()

    foo = Foo.objects.create(text="hello")
    url = reverse("foo", args=(foo.ekey,))
    response = client.get(url)
    assert response.status_code == 200
    response_object = response.context["object"]
    assert response_object == foo
