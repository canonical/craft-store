.. _howto:

How-to guides
*************

.. toctree::
   :maxdepth: 1


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


Using craft-cli for upload progress
===================================

Progress can be provided by use of craft-cli_. This example will upload
``./test.snap`` with something that looks like the following:

.. code-block:: python

  #!/usr/bin/env python
  from pathlib import Path

  from craft_cli import emit, EmitterMode
  from craft_store import StoreClient, endpoints
  from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


  emit.init(EmitterMode.NORMAL, "craft.store-howto", "Starting howto app.")

  store_client = StoreClient(
      base_url="https://dashboard.staging.snapcraft.io",
      storage_base_url="https://upload.apps.staging.ubuntu.com",
      endpoints=endpoints.SNAP_STORE,
      user_agent="Craft Store Howto Agent",
      application_name="craft-store-upload",
  )


  def create_callback(encoder: MultipartEncoder):
      with emit.progress_bar("Uploading...", encoder.len, delta=False) as progress:

          def progress_callback(monitor: MultipartEncoderMonitor):
              progress.advance(monitor.bytes_read)

      return progress_callback


  upload_id = store_client.upload_file(
      monitor_callback=create_callback,
      filepath=Path("test.snap"),
  )

  emit.message(f"upload-id: {upload_id}", intermediate=True)
  emit.ended_ok()



.. _craft-cli: https://craft-cli.readthedocs.org/
