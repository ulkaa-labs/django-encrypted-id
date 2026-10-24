from django.db import models

from encrypted_id.models import EncryptedIDModel, EncryptedIDManager


class Foo(EncryptedIDModel):
    text = models.TextField()

    class Meta:
        db_table = "xxx"


class Foo2Manager(EncryptedIDManager):
    pass


class Foo2(EncryptedIDModel):
    text = models.TextField()

    class Meta:
        db_table = "yyy"
        ek_key = "xxx"


class Bar(EncryptedIDModel):
    text = models.TextField()


class BigItem(EncryptedIDModel):
    """BigAutoField model — ekey OK, skey only when pk < 2**32."""

    id = models.BigAutoField(primary_key=True)
    text = models.TextField()

    class Meta:
        db_table = "big_item"
