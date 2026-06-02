.. _howto-login_ubuntu_one_keyring:

Log in to Charmhub with Ubuntu One
==================================

This guide shows you how to log in to Charmhub using your Ubuntu One credentials and
how to save those credentials securely in your system keyring. This allows you to
retrieve them in future sessions without re-entering your password.

Prerequisites
-------------

Before you begin, ensure you have:

*   An Ubuntu One account.
*   The ``craft-store`` library installed.
*   A functional system keyring, such as GNOME Keyring or KWallet.

Initialize the login client
---------------------------

Create an instance of ``UbuntuOneLogin``, providing the API base URL for Charmhub.

.. code-block:: python

   from craft_store.login import UbuntuOneLogin

   login_client = UbuntuOneLogin("https://api.charmhub.io")

Authenticate and save credentials
---------------------------------

Use the ``login_with`` method to authenticate. This method requests a macaroon from
Charmhub, discharges it using your Ubuntu One credentials, and saves the resulting
root/discharge macaroon pair in your system keyring.

.. code-block:: python

   login_client.login_with(
       email="<email>",
       password="<password>",
       api_base_url="https://api.charmhub.io",
       otp="<otp>",  # Optional: required if two-factor authentication is enabled
       permissions=["account-view-packages", "account-register-package"]
   )

Replace ``<email>``, ``<password>``, and ``<otp>`` with your actual credentials.

Retrieve credentials from the keyring
-------------------------------------

To use the saved credentials later, initialize an ``Auth`` object. Use the
application name ``craft-store-ubuntu-one`` and the host ``api.charmhub.io``.

.. code-block:: python

   from craft_store import Auth, UbuntuOneAuth, publisher

   auth = Auth(
       application_name="craft-store-ubuntu-one",
       host="api.charmhub.io"
   )

The ``Auth`` object automatically looks for credentials in your system keyring that
match the provided application name and host.

Use the credentials with a store client
---------------------------------------

Pass the ``Auth`` object to a store gateway to perform authenticated actions.

.. code-block:: python

   from craft_store import UbuntuOneAuth, publisher

   gateway = publisher.PublisherGateway(
       base_url="https://api.charmhub.io",
       namespace="charm",
       auth=auth,
       httpx_auth=UbuntuOneAuth(auth=auth, api_base_url="https://api.charmhub.io"),
   )

   # List your registered charms
   for charm in gateway.list_registered_names(include_collaborations=True):
       print(f"{charm.name} [{charm.status}]")

Verify your login
-----------------

You can use the ``whoami()`` method to verify that you're logged in and to retrieve
information about your account.

.. code-block:: python

   user_info = gateway.whoami()
   print(f"Logged in as: {user_info['account']['display-name']}")

Handle login errors
-------------------

The ``login_with`` method can raise specific errors if the authentication fails.

.. code-block:: python

   from craft_store import errors

   try:
       login_client.login_with(...)
   except errors.UbuntuOneOtpRequiredError:
       print("Your account requires two-factor authentication. Please provide an OTP.")
   except errors.UbuntuOneCredentialsError:
       print("Invalid email, password, or OTP.")

Handle missing credentials
--------------------------

If you try to retrieve credentials that aren't in the keyring, ``Auth`` raises a
``CredentialsUnavailable`` error. You should catch this error to prompt the user to
log in.

.. code-block:: python

   from craft_store import errors

   try:
       # This happens automatically when the gateway uses auth
       names = gateway.list_registered_names()
   except errors.CredentialsUnavailable:
       print("No credentials found. Please run the login step first.")
