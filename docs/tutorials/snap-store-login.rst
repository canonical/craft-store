.. _tutorial-snap_store_login:

Login to the Snap Store
=======================

Prerequisites
-------------

- Python 3.8 or 3.9
- a clean virtual environment setup
- a text editor
- a developer account on https://snapcraft.io


Setup
-----

Enable the virtual environment and then install Craft Store by running::

  $ pip install craft-store

Code
----

Write following into a a text editor and save it as ``snap_store_login.py``:

.. code-block:: python

  #!/usr/bin/env python
  from craft_store import StoreClient, endpoints

  store_client = StoreClient(
      base_url="https://dashboard.snapcraft.io",
      storage_base_url="https://upload.apps.staging.ubuntu.com",
      endpoints=endpoints.SNAP_STORE,
      user_agent="Craft Store Tutorial Agent",
      application_name="cart-store-tutorial"
  )

  store_client.login(
      permissions=["package_access"],
      description="tutorial-client-login",
      ttl=1000
  )

Run
---

Run the saved python module to login::

  $ python snap_store_login.py
