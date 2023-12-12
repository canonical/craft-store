.. _howto-craft_cli_upload_progress:

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
