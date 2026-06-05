#!/usr/bin/env python3

"""Demo of Ubuntu One login with craft-store."""

import getpass
import logging
import os
import sys
from urllib.parse import urlparse

from craft_store import Auth, UbuntuOneAuth, errors, publisher
from craft_store.login import UbuntuOneLogin

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the login demo."""
    logging.basicConfig(level=logging.INFO)

    api_base_url = os.getenv("CRAFT_STORE_CHARMHUB", "https://api.charmhub.io")
    login_url = os.getenv("CRAFT_LOGIN_URL", "https://login.ubuntu.com")
    host = urlparse(api_base_url).netloc
    application_name = "craft-store-ubuntu-one"

    email = os.getenv("USSO_USER") or input("Email address: ").strip()
    password = os.getenv("USSO_PW") or getpass.getpass("Password: ")
    otp = os.getenv("USSO_OTP") or None
    if otp is None:
        otp = input("OTP (optional): ").strip() or None

    try:
        # login_with is a classmethod that returns (root, discharged)
        # and automatically saves the credentials to the keyring.
        # Use the same application_name that will be used later!
        UbuntuOneLogin.login_with(
            email=email,
            password=password,
            api_base_url=api_base_url,
            login_url=login_url,
            application_name=application_name,
            otp=otp,
            permissions=["account-view-packages", "account-register-package"],
        )
    except errors.UbuntuOneCredentialsError as e:
        print(f"Login failed: {e}", file=sys.stderr)
        sys.exit(1)
    except errors.UbuntuOneOtpRequiredError as e:
        print(f"Two-factor authentication required: {e}", file=sys.stderr)
        sys.exit(1)

    # Use the saved credentials with PublisherGateway.
    # We use UbuntuOneAuth which handles the exchange internally.
    # Important: use the same application_name that was used during login!
    u1_auth = Auth(
        application_name=application_name,
        host=host,
        file_fallback=True,
    )

    gateway = publisher.PublisherGateway(
        base_url=api_base_url,
        namespace="charm",
        auth=u1_auth,
        httpx_auth=UbuntuOneAuth(auth=u1_auth, api_base_url=api_base_url),
    )

    try:
        user_info = gateway.whoami()
    except errors.CraftStoreError as e:
        print(f"Failed to retrieve user information: {e}", file=sys.stderr)
        logger.exception("Full traceback:")
        sys.exit(1)

    account = user_info.get("account", {}) or {}
    display_name = account.get("display-name")
    email_addr = account.get("email")
    print(f"Logged in as: {display_name} ({email_addr})")

    for charm in gateway.list_registered_names(include_collaborations=True):
        print(f"{charm.name} [{charm.status}]")


if __name__ == "__main__":
    main()
