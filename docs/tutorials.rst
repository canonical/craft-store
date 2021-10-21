*********
Tutorials
*********

.. tutorial-snap_store_login:
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


Get Account email and id from the Snap Store
============================================

Prerequisites
-------------

- Completed :ref:`tutorial-snap_store_login`
- Shelled into the virtual environment created in :ref:`tutorial-snap_store_login`

Code
----

Write following into a a text editor and save it as ``snap_store_whoami.py``:

.. code-block:: python

  #!/usr/bin/env python
  from craft_store import StoreClient, endpoints

  store_client = StoreClient(
      base_url="https://dashboard.snapcraft.io",
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

  $ python snap_store_login.py
