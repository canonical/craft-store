.. _tutorial-snap_store_login_ubuntu_one:

Login to the Snap Store using Ubuntu One
========================================

At the end of this tutorial you will have successfully written a
script that can log you into the Snap Store using Ubuntu One
(https://login.ubuntu.com) and have those credentials stored for the
combination of the `Snapcraft Dashboard`_ and
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

Write following into a a text editor and save it as
``snap_store_login_ubuntu_one.py``:

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

.. _Snapcraft Dashboard: https://dashboard.snapcraft.io/stores/snaps/
