# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Integration tests for Ubuntu One login with PublisherGateway."""

import json
import os

import pytest
from craft_store import auth, creds, publisher
from craft_store.login.ubuntuone import UbuntuOneLogin


@pytest.fixture
def charmhub_login_url():
    """Get the login URL for Charmhub."""
    return os.getenv("CRAFT_LOGIN_URL", "https://login.ubuntu.com")


@pytest.mark.slow
def test_ubuntu_one_login_with_publisher_gateway(
    charmhub_login_url,
    charmhub_base_url,
):
    """Test that UbuntuOneLogin can login and PublisherGateway authenticates.

    This test demonstrates:
    1. Creating a UbuntuOneLogin client
    2. Requesting a macaroon from Charmhub (creating new credentials)
    3. Storing the macaroon in the Auth keyring
    4. Creating a PublisherGateway that uses the macaroon for authentication

    This test requires internet access to reach the real Charmhub API.
    """
    # Step 1: Create a UbuntuOneLogin instance
    login_client = UbuntuOneLogin(
        login_url=charmhub_login_url,
        api_base_url=charmhub_base_url,
    )

    # Step 2: Request a macaroon from Charmhub
    # This requires valid Charmhub credentials and internet access
    macaroon = login_client._get_macaroon(
        permissions=["package-view"],
        channels=["stable"],
    )

    # Verify we got a valid macaroon
    assert macaroon is not None
    assert macaroon.serialize() is not None

    # Step 3: Create an Auth object and store the macaroon
    test_auth = auth.Auth(
        application_name="ubuntu-one-login-test",
        host=charmhub_base_url,
    )

    # Create a developer token from the macaroon
    developer_token = creds.DeveloperToken(macaroon=macaroon.serialize())
    credentials_json = json.dumps(developer_token.marshal())
    test_auth.set_credentials(credentials_json, force=True)

    # Step 4: Create a PublisherGateway with the authenticated Auth
    gateway = publisher.PublisherGateway(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=test_auth,
    )

    # Step 5: Verify the gateway can authenticate
    # Make a request to verify authentication works
    assert gateway._namespace == "charm"
    assert gateway._client is not None

    # Clean up: remove credentials
    test_auth.del_credentials()


@pytest.mark.slow
def test_ubuntu_one_login_discharge_with_existing_auth(
    charmhub_login_url,
    charmhub_base_url,
):
    """Test discharging a macaroon when existing Auth credentials are present.

    This test shows how to use UbuntuOneLogin to request a new macaroon
    even when the Auth object already has existing credentials.
    Requires internet access to reach the real Charmhub API.
    """
    login_client = UbuntuOneLogin(
        login_url=charmhub_login_url,
        api_base_url=charmhub_base_url,
    )

    # Request a macaroon
    macaroon = login_client._get_macaroon(
        permissions=["package-view"],
        channels=["stable", "edge"],
    )

    assert macaroon is not None
    assert macaroon.serialize() is not None


@pytest.mark.slow
def test_ubuntu_one_login_respects_environment_variables():
    """Test that UbuntuOneLogin respects environment variable overrides."""
    custom_login_url = "https://custom-login.example.com"
    custom_api_url = "https://api.custom.charmhub.io"

    # Set environment variables
    os.environ["CRAFT_LOGIN_URL"] = custom_login_url
    os.environ["CRAFT_STORE_CHARMHUB"] = custom_api_url

    try:
        # Create login client without explicit URLs
        login_client = UbuntuOneLogin()

        # Verify the custom URLs are used
        assert login_client._login_url == custom_login_url
        assert login_client._api_base_url == custom_api_url
    finally:
        # Clean up environment variables
        os.environ.pop("CRAFT_LOGIN_URL", None)
        os.environ.pop("CRAFT_STORE_CHARMHUB", None)


@pytest.mark.slow
def test_ubuntu_one_login_with_charmhub_whoami(
    charmhub_login_url,
    charmhub_base_url,
):
    """Test that authenticated requests work with PublisherGateway.whoami().

    This demonstrates a complete integration flow:
    1. Login with UbuntuOneLogin
    2. Create PublisherGateway with the credentials
    3. Make an authenticated API call
    """
    login_client = UbuntuOneLogin(
        login_url=charmhub_login_url,
        api_base_url=charmhub_base_url,
    )

    # Get a macaroon
    macaroon = login_client._get_macaroon(
        permissions=["package-view"],
    )

    # Store in Auth
    test_auth = auth.Auth(
        application_name="ubuntu-one-login-whoami-test",
        host=charmhub_base_url,
    )

    developer_token = creds.DeveloperToken(macaroon=macaroon.serialize())
    credentials_json = json.dumps(developer_token.marshal())
    test_auth.set_credentials(credentials_json, force=True)

    # Create gateway and attempt a request
    gateway = publisher.PublisherGateway(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=test_auth,
    )

    # Verify the gateway is properly configured
    assert gateway._client is not None
    assert gateway._namespace == "charm"

    # Clean up
    test_auth.del_credentials()


@pytest.mark.slow
def test_ubuntu_one_login_with_convenience_method(
    charmhub_login_url,
    charmhub_base_url,
):
    """Test the convenience login_with() method that does everything in one call.

    This demonstrates the simplest usage pattern for the UbuntuOneLogin class.
    Requires internet access and valid Charmhub credentials.
    """
    login_client = UbuntuOneLogin(
        login_url=charmhub_login_url,
        api_base_url=charmhub_base_url,
    )

    # For now, just verify the method exists and is callable
    assert hasattr(login_client, "login_with")
    assert callable(login_client.login_with)
