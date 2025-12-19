.. _howto-environment_credentials:

Using credentials provided by an environment variable
=====================================================

Retrieving the credentials
--------------------------

Use the following snippet to obtain general credentials for your account:

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

  print(f"Exported credentials: {credentials}")


.. note::

   The :meth:`craft_store.store_client.StoreClient.login` method has some
   extra parameters such as ``packages`` and ``channels`` to restrict the
   credentials *reach* even further. Also take consideration into further
   locking down ``permissions`` (:mod:`craft_store.attenuations`).


Using retrieved credentials
---------------------------

If :class:`craft_store.store_client.StoreClient` is initialized with
``environment_auth`` and the value is set then a in-memory
keyring is used instead of the system keyring.

To make use of such thing, export ``CREDENTIALS=<credentials>`` where
``<credentials>`` is the recently retrieved credential. To make use of
it and get information from your account:


.. code-block:: python

  #!/usr/bin/env python
  from craft_store import StoreClient, endpoints

  store_client = StoreClient(
      base_url="https://dashboard.snapcraft.io",
      endpoints=endpoints.SNAP_STORE,
      user_agent="Craft Store Tutorial Agent",
      application_name="cart-store-tutorial",
      environment_auth="CREDENTIALS",
  )

  whoami = store_client.whoami()

  print(f"email: {whoami['account']['email']}")
  print(f"id: {whoami['account']['id']}")
