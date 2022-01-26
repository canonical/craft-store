*********
Tutorials
*********

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


Login to the Snap Store using Ubuntu One
========================================

At the end of this tutorial you will have successfully written a
script that can log you into the Snap Store using Ubuntu One
(https://login.ubuntu.com) and have those credentials stored for the
combination of Dashboard endpoint (https://dashboard.snapcraft.io) and
application name (``ubuntu1-dashboard``).

Prerequisites
-------------

- Python 3.8 or 3.9
- a clean virtual environment setup
- a text editor
- a developer account on https://snapcraft.io


Setup
-----

Enable the virtual environment and then install Craft Store by running::

  $ pip install craft-store click

Code
----

Write following into a a text editor and save it as ``snap_store_login_ubuntu_one.py``:

.. code-block:: python

  import click

  from craft_store import *

  c = UbuntuOneStoreClient(
      base_url="https://dashboard.snapcraft.io",
      storage_base_url="https://upload.apps.staging.ubuntu.com",
      auth_url="https://login.ubuntu.com",
      endpoints=endpoints.U1_SNAP_STORE,
      application_name="ubuntu1-dashboard",
      user_agent="test",
  )

  email = click.prompt("Email")
  password = click.prompt("Password", hide_input=True)

  try:
      c.login(
          permissions=[
              "package_access",
              "package_manage",
              "package_metrics",
              "package_push",
              "package_register",
              "package_release",
              "package_update",
          ],
          description="foo",
          ttl=1800,
          email=email,
          password=password,
      )
  except errors.StoreServerError as server_error:
      if "twofactor-required" in server_error.error_list:
          otp = click.prompt("OTP")
          c.login(
              permissions=[
                  "package_access",
                  "package_manage",
                  "package_metrics",
                  "package_push",
                  "package_register",
                  "package_release",
                  "package_update",
              ],
              description="foo",
              ttl=1800,
              email=email,
              password=password,
              otp=otp,
          )

Run
---

Run the saved python module to login::

  $ python snap_store_login_ubuntu_one.py


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

Open a text editor to add logic to instantiate a StoreClient for the Staging Snap
Store:

.. code-block:: python

  #!/usr/bin/env python
  from pathlib import Path

  from craft_store import StoreClient, endpoints

  store_client = StoreClient(
      base_url="https://dashboard.staging.snapcraft.io",
      storage_base_url="https://upload.apps.staging.ubuntu.com",
      endpoints=endpoints.SNAP_STORE,
      user_agent="Craft Store Tutorial Agent",
      application_name="cart-store-tutorial"
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
  from requests_toolbelt import MultipartEncoderMonitor

  def progress_callback(monitor: MultipartEncoderMonitor) -> None:
      print(f"Uploaded: {monitor.bytes_read} of {monitor.len}")


  store_client = StoreClient(
      base_url="https://dashboard.staging.snapcraft.io",
      storage_base_url="https://upload.apps.staging.ubuntu.com",
      endpoints=endpoints.SNAP_STORE,
      user_agent="Craft Store Tutorial Agent",
      application_name="cart-store-tutorial"
  )

  upload_id = store_client.upload_file(
       filepath=Path("/tmp/hello.snap"),
       monitor_callback=progress_callback
  )

  print(f"upload-id: {upload_id}")

Save the file.

Run
---

Run the saved python module again to upload the *hello* snap and obtain an upload-id
at the end, but observing progress as the upload takes place::

  $ python snap_store_upload.py
