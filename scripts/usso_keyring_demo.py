#!/usr/bin/env python3

"""Demo of Ubuntu One keyring integration with craft-store."""

import os
from urllib.parse import urlparse

from craft_store import Auth, UbuntuOneAuth, errors, publisher


def main() -> None:
    """Run the keyring demo."""
    api_base_url = os.getenv("CRAFT_STORE_CHARMHUB", "https://api.charmhub.io")
    host = urlparse(api_base_url).netloc

    auth = Auth(
        application_name="craft-store-ubuntu-one",
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
        print(
            f"Logged in as: {user_info.get('account', {}).get('display-name')} ({user_info.get('account', {}).get('email')})"
        )

        for charm in gateway.list_registered_names(include_collaborations=True):
            print(f"{charm.name} [{charm.status}]")
    except errors.CredentialsUnavailable:
        raise SystemExit(
            "No Ubuntu One credentials found in the keyring. Run usso_login_demo first."
        )


if __name__ == "__main__":
    main()
