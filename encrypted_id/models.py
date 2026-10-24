"""Model mixins and managers that expose encrypted primary keys (ekey / skey)."""

from django.db import models
from django.db.models import options

from encrypted_id import (
    EncryptedIDDecodeError,
    coerce_int_pk,
    encode_ekey,
    encode_skey,
    decode_ekey,
    decode_skey,
    get_object_or_404,
    get_object_or_404_skey,
    get_model_sub_key,
)

if "ek_key" not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES += ("ek_key",)


class EncryptedIDManager(models.Manager):
    def get_by_ekey(self, ekey, **kw):
        return self.get(pk=decode_ekey(ekey, get_model_sub_key(self.model)), **kw)

    def get_by_ekey_or_404(self, *args, **kw):
        return get_object_or_404(self.model, *args, **kw)

    def get_by_skey(self, skey, **kw):
        return self.get(pk=decode_skey(skey, get_model_sub_key(self.model)), **kw)

    def get_by_skey_or_404(self, *args, **kw):
        return get_object_or_404_skey(self.model, *args, **kw)


class EncryptedIDQuerySet(models.QuerySet):
    """QuerySet that accepts ``ekey=`` / ``skey=`` lookups like a PK field."""

    def _resolve_encrypted_lookups(self, kwargs):
        """Rewrite ekey/skey kwargs to pk.

        Returns ``(kwargs, ok)``. When ``ok`` is False the lookup cannot match
        any row (invalid / forged token).
        """
        kwargs = dict(kwargs)
        sub_key = get_model_sub_key(self.model)
        resolved = []

        if "ekey" in kwargs:
            token = kwargs.pop("ekey")
            try:
                if token is None:
                    raise EncryptedIDDecodeError()
                resolved.append(decode_ekey(token, sub_key))
            except EncryptedIDDecodeError:
                return kwargs, False

        if "skey" in kwargs:
            token = kwargs.pop("skey")
            try:
                if token is None:
                    raise EncryptedIDDecodeError()
                resolved.append(decode_skey(token, sub_key))
            except EncryptedIDDecodeError:
                return kwargs, False

        if len(resolved) == 2 and resolved[0] != resolved[1]:
            return kwargs, False
        if resolved:
            kwargs["pk"] = resolved[0]
        return kwargs, True

    def filter(self, *args, **kwargs):
        kwargs, ok = self._resolve_encrypted_lookups(kwargs)
        if not ok:
            return self.none()
        return super().filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        kwargs, ok = self._resolve_encrypted_lookups(kwargs)
        if not ok:
            # Invalid token matches nothing, so excluding it is a no-op.
            if not args and not kwargs:
                return self
            return super().exclude(*args, **kwargs)
        return super().exclude(*args, **kwargs)


class EncryptedIDModel(models.Model):
    class Meta:
        abstract = True

    objects = EncryptedIDManager.from_queryset(EncryptedIDQuerySet)()

    @property
    def ekey(self):
        return encode_ekey(
            coerce_int_pk(self.pk, for_skey=False),
            get_model_sub_key(self),
        )

    @property
    def skey(self):
        return encode_skey(
            coerce_int_pk(self.pk, for_skey=True),
            get_model_sub_key(self),
        )
