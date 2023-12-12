.. _tutorial-snap_store_account_info:

Get Account email and id from the Snap Store
============================================

Prerequisites
-------------

- Completed :ref:`tutorial-snap_store_login`
- Shelled into the virtual environment created in
  :ref:`tutorial-snap_store_login`

Code
----

Write following into a a text editor and save it as ``snap_store_whoami.py``:

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

  whoami = store_client.whoami()

  print(f"email: {whoami['account']['email']}")
  print(f"id: {whoami['account']['id']}")

Run
---

Run the saved python module to retrieved the account information for the login::

  $ python snap_store_whoami.py
