.. _tutorial-upload_snap:

Upload a snap to storage
========================

At the end of this tutorial you will be able to upload a snap to file storage
and see simple progress and total length updated on the screen as the upload
takes place.

Prerequisites
-------------

- Python 3.8
- a clean virtual environment setup
- a text editor


Setup
-----

Create a clean virtual environment::

  $ pip3 -m venv ~/craft-store-upload
  $ . ~/craft-store-upload/bin/activate

Install Craft Store by running::

  $ pip install craft-store

Obtain a snap to upload by downloading one from the Snap Store and give it a
predictable name::

  $ snap download hello
  $ mv hello_*.snap /tmp/hello.snap


Code for uploading
------------------

Open a text editor to add logic to instantiate a StoreClient for the Staging
Snap Store:

.. code-block:: python

  #!/usr/bin/env python
  from pathlib import Path

  from craft_store import StoreClient, endpoints

  store_client = StoreClient(
      base_url="https://dashboard.staging.snapcraft.io",
      storage_base_url="https://upload.apps.staging.ubuntu.com",
      endpoints=endpoints.SNAP_STORE,
      user_agent="Craft Store Tutorial Agent",
      application_name="craft-store-tutorial"
  )

  upload_id = store_client.upload_file(filepath=Path("/tmp/hello.snap"))

  print(f"upload-id: {upload_id}")


Save the file as ``snap_store_upload.py``:

Run
---

Run the saved python module to upload the *hello* snap and obtain an upload-id
at the end::

  $ python snap_store_upload.py

Adding progress
---------------

Now add a mechanism to view progress for the upload, open the recently saved
``snap_store_upload.py`` file and modify it so that it looks like the following:

.. code-block:: python

  #!/usr/bin/env python
  from pathlib import Path

  from craft_store import StoreClient, endpoints
  from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


  def monitor_callback(encoder: MultipartEncoder) -> None:
      def progress_callback(monitor: MultipartEncoderMonitor) -> None:
          print(f"Uploaded: {monitor.bytes_read} of {monitor.len}")

      return progress_callback


  store_client = StoreClient(
      base_url="https://dashboard.staging.snapcraft.io",
      storage_base_url="https://upload.apps.staging.ubuntu.com",
      endpoints=endpoints.SNAP_STORE,
      user_agent="Craft Store Tutorial Agent",
      application_name="craft-store-tutorial"
  )

  upload_id = store_client.upload_file(
       filepath=Path("/tmp/hello.snap"),
       monitor_callback=progress_callback
  )

  print(f"upload-id: {upload_id}")

Save the file.

Run
---

Run the saved python module again to upload the *hello* snap and obtain an
upload-id at the end, but observing progress as the upload takes place::

  $ python snap_store_upload.py
