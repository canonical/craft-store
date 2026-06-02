#!/usr/bin/env python3

"""Demo of Ubuntu One login with craft-store."""

import getpass
import os
from urllib.parse import urlparse

from craft_store import Auth, DeveloperTokenAuth, publisher
from craft_store.login import UbuntuOneLogin


def main() -> None:
    """Run the login demo."""
    api_base_url = os.getenv("CRAFT_STORE_CHARMHUB", "https://api.charmhub.io")
    host = urlparse(api_base_url).netloc

    email = os.getenv("USSO_USER") or input("Email address: ").strip()
    password = os.getenv("USSO_PW") or getpass.getpass("Password: ")
    otp = os.getenv("USSO_OTP") or None
    if otp is None:
        otp = input("OTP (optional): ").strip() or None

    # login_with is a classmethod that returns (root, discharged)
    # and automatically saves the credentials to the default Auth keyring.
    UbuntuOneLogin.login_with(
        email=email,
        password=password,
        api_base_url=api_base_url,
        otp=otp,
        permissions=["account-view-packages", "account-register-package"],
    )

    # The store token is saved in a specific keyring application name by UbuntuOneLogin
    auth = Auth(
        application_name="craft-store-ubuntu-one-store-token",
        host=host,
        file_fallback=True,
    )

    gateway = publisher.PublisherGateway(
        base_url=api_base_url,
        namespace="charm",
        auth=auth,
        httpx_auth=DeveloperTokenAuth(auth=auth, auth_type="macaroon"),
    )

    user_info = gateway.whoami()
    print(
        f"Logged in as: {user_info.get('account', {}).get('display-name')} ({user_info.get('account', {}).get('email')})"
    )

    for charm in gateway.list_registered_names(include_collaborations=True):
        print(f"{charm.name} [{charm.status}]")


if __name__ == "__main__":
    main()
