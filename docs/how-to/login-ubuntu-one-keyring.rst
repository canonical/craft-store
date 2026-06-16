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

Authenticate and save credentials
----------------------------------

Use :meth:`~craft_store.login.UbuntuOneLogin.login_with` to authenticate. This method
requests a macaroon from Charmhub, discharges it using your Ubuntu One credentials,
and saves the resulting root/discharge macaroon pair in your system keyring.

.. code-block:: python

   from craft_store.login import UbuntuOneLogin

   UbuntuOneLogin.login_with(
       email="<email>",
       password="<password>",
       base_url="https://api.charmhub.io",
       permissions=["account-view-packages", "account-register-package"],
   )

Replace ``<email>`` and ``<password>`` with your actual credentials.

Authenticate with OTP
~~~~~~~~~~~~~~~~~~~~~

If your account has two-factor authentication enabled, the first call will raise
:exc:`~craft_store.login.UbuntuOneOtpRequiredError`. Retry with your one-time
password using the ``otp`` argument:

.. code-block:: python

   from craft_store.login import UbuntuOneLogin, UbuntuOneOtpRequiredError

   try:
       UbuntuOneLogin.login_with(
           email="<email>",
           password="<password>",
           base_url="https://api.charmhub.io",
           permissions=["account-view-packages", "account-register-package"],
       )
   except UbuntuOneOtpRequiredError:
       UbuntuOneLogin.login_with(
           email="<email>",
           password="<password>",
           base_url="https://api.charmhub.io",
           permissions=["account-view-packages", "account-register-package"],
           otp="<otp>",
       )

Use the credentials with a store client
---------------------------------------

Use :meth:`~craft_store.publisher.PublisherGateway.with_ubuntu_one` to create a
gateway that reads your saved credentials from the keyring automatically.

.. code-block:: python

   from craft_store.publisher import PublisherGateway

   gateway = PublisherGateway.with_ubuntu_one(
       base_url="https://api.charmhub.io",
       namespace="charm",
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

   from craft_store.login import (
       UbuntuOneLogin,
       UbuntuOneCredentialsError,
       UbuntuOneOtpRequiredError,
   )

   try:
       UbuntuOneLogin.login_with(...)
   except UbuntuOneOtpRequiredError:
       print("Your account requires two-factor authentication. Please provide an OTP.")
   except UbuntuOneCredentialsError:
       print("Invalid email, password, or OTP.")

Handle missing credentials
--------------------------

If you try to use the gateway but no credentials are found in the keyring,
``PublisherGateway.with_ubuntu_one`` will succeed but the first API call will
raise a ``CredentialsUnavailable`` error. Catch this error to prompt the user to
log in.

.. code-block:: python

   from craft_store import errors

   try:
       names = gateway.list_registered_names()
   except errors.CredentialsUnavailable:
       print("No credentials found. Run the login step first.")
