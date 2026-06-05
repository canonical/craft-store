#!/usr/bin/env python3

"""Demo of Ubuntu One keyring integration with craft-store."""

import os
from urllib.parse import urlparse

from craft_store import Auth, UbuntuOneAuth, errors, publisher


def main() -> None:
    """Run the keyring demo.

    This demonstrates retrieving Ubuntu One credentials from the keyring.
    After running usso_login_demo.py, this script will retrieve the same
    credentials and use them for API calls. The exchanged store token is
    cached in the keyring to avoid re-exchanging the one-time-use macaroons.
    """
    api_base_url = os.getenv("CRAFT_STORE_CHARMHUB", "https://api.charmhub.io")
    host = urlparse(api_base_url).netloc
    # Use the same application_name as the login demo so we use the same credentials
    application_name = "craft-store-ubuntu-one"

    auth = Auth(
        application_name=application_name,
        host=host,
        file_fallback=True,
    )
    gateway = publisher.PublisherGateway(
        base_url=api_base_url,
        namespace="charm",
        auth=auth,
        httpx_auth=UbuntuOneAuth(auth=auth, api_base_url=api_base_url),
    )

    try:
        user_info = gateway.whoami()
        account = user_info.get("account", {}) or {}
        display_name = account.get("display-name")
        email_addr = account.get("email")
        print(f"Logged in as: {display_name} ({email_addr})")

        for charm in gateway.list_registered_names(include_collaborations=True):
            print(f"{charm.name} [{charm.status}]")
    except errors.CredentialsUnavailable:
        raise SystemExit(
            f"No Ubuntu One credentials found in the keyring for application '{application_name}'. "
            "Run usso_login_demo.py first to store credentials."
        )


if __name__ == "__main__":
    main()
