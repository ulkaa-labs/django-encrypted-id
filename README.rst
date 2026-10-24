django-encrypted-id
===================

Encrypt Django model primary keys into URL-safe tokens.

========  =========  ==========================================  =========
Token     Length     Algorithm                                   ID range
========  =========  ==========================================  =========
``ekey``  32 chars   AES-256-SIV (authenticated, deterministic)  64-bit
``skey``  9 chars    Feistel + HMAC + base62                     32-bit
========  =========  ==========================================  =========

Requires **Python 3.10+** and **Django 5.2+**.


Installation
------------

.. code-block:: bash

    pip install .

Or from a checkout / private index, add this package to your project
dependencies. Runtime deps are declared in ``pyproject.toml``:

* ``Django>=5.2,<6``
* ``pycryptodomex>=3.15``

Do **not** add ``encrypted_id`` to ``INSTALLED_APPS``.


Quick start
-----------

.. code-block:: python

    from django.db import models
    from encrypted_id.models import EncryptedIDModel


    class Order(EncryptedIDModel):
        class Meta:
            ek_key = "orders-v1"  # optional; defaults to db_table


.. code-block:: python

    >>> order = Order.objects.create(...)
    >>> order.ekey   # 32-char token — prefer this
    >>> order.skey   # 9-char token — only if pk < 2**32

    Order.objects.get_by_ekey(order.ekey)
    Order.objects.get_by_skey(order.skey)
    Order.objects.get(ekey=order.ekey)
    Order.objects.filter(skey=order.skey)


Helpers (no model mixin required):

.. code-block:: python

    from encrypted_id import (
        ekey, skey,
        encode_ekey, decode_ekey,
        encode_skey, decode_skey,
        get_object_or_404, get_object_or_404_skey,
    )

    ekey(instance)                 # encode_ekey(instance.pk, sub_key)
    skey(instance)                 # encode_skey(instance.pk, sub_key)
    get_object_or_404(Order, token)
    get_object_or_404_skey(Order, token)


URL patterns
------------

.. code-block:: python

    from django.urls import re_path

    re_path(r"^o/(?P<slug>[0-9A-Za-z_-]{32})/$", ...)  # ekey
    re_path(r"^o/(?P<slug>[0-9A-Za-z]{9})/$", ...)     # skey


When to use which
-----------------

* **ekey** — default. Full 64-bit pk space, authenticated encryption.
* **skey** — short links / QR / SMS. Requires ``pk < 2**32`` (``AutoField``).
  Prefer ``ekey`` with ``BigAutoField``.


Secret key rotation
-------------------

.. code-block:: python

    # settings.py
    SECRET_KEY = "new-secret-..."
    SECRET_KEYS = [
        SECRET_KEY,
        "previous-secret-...",
    ]


Production notes
----------------

* Keep ``SECRET_KEY`` private. Rotating it without old values in
  ``SECRET_KEYS`` invalidates every issued token.
* ``ekey`` is AES-SIV authenticated — tampered tokens fail closed.
* ``skey`` uses a 16-bit MAC to stay in 9 characters; obscure sequential
  ids only. Always enforce object-level permissions in views.
* Different models get different tokens for the same numeric pk unless they
  share ``Meta.ek_key``.
* Legacy CBC+CRC tokens (≤ 0.3.x, 22 chars) remain readable via ``encode`` /
  ``decode``. Model ``.ekey`` uses the new AES-SIV format.


Development
-----------

.. code-block:: bash

    python3.13 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    pip install Django==5.2.17
    pytest

Multi-version::

    tox

Layout::

    encrypted_id/     # installable package
    tests/            # pytest + Django test project
    pyproject.toml    # packaging + pytest config
    tox.ini           # local multi-Python runs
    .github/          # CI
