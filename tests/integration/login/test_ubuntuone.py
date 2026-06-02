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

import os
from urllib.parse import urlparse

import keyring
import pytest
from craft_store import DeveloperTokenAuth, UbuntuOneAuth, auth, publisher
from craft_store.auth import MemoryKeyring
from craft_store.login import UbuntuOneLogin


@pytest.fixture(autouse=True)
def _test_keyring():
    """In memory keyring backend for testing."""
    current_keyring = keyring.get_keyring()
    keyring.set_keyring(MemoryKeyring())
    yield
    keyring.set_keyring(current_keyring)


@pytest.fixture
def charmhub_login_url():
    """Get the login URL for Charmhub."""
    return os.getenv("CRAFT_LOGIN_URL", "https://login.staging.ubuntu.com")


@pytest.fixture
def staging_sso_credentials():
    """Get staging SSO credentials from environment."""
    email = os.getenv("STAGING_SSO_USERNAME")
    password = os.getenv("STAGING_SSO_PASSWORD")
    if not email or not password:
        pytest.skip("STAGING_SSO_USERNAME and STAGING_SSO_PASSWORD are not set")
    return email, password


@pytest.mark.slow
def test_ubuntu_one_login_smoke(
    charmhub_login_url,
    charmhub_base_url,
):
    """Smoke test for UbuntuOneLogin and PublisherGateway connectivity.

    This test verifies that:
    1. A UbuntuOneLogin client can be created.
    2. An unsigned macaroon can be requested from the store API.
    3. A PublisherGateway can be correctly instantiated.

    This test requires internet access to reach the real Charmhub API,
    but does not require valid Ubuntu One credentials.
    """
    # Step 1: Create a UbuntuOneLogin instance
    login_client = UbuntuOneLogin(
        api_base_url=charmhub_base_url,
        login_url=charmhub_login_url,
    )

    # Step 2: Request an unsigned macaroon
    macaroon = login_client._get_macaroon(
        permissions=["package-view"],
    )

    # Verify we got a valid macaroon
    assert macaroon is not None
    assert macaroon.serialize() is not None

    # Step 3: Verify PublisherGateway can be configured
    test_auth = auth.Auth(
        application_name="ubuntu-one-login-smoke-test",
        host=urlparse(charmhub_base_url).netloc,
        file_fallback=True,
    )
    gateway = publisher.PublisherGateway(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=test_auth,
        httpx_auth=DeveloperTokenAuth(auth=test_auth, auth_type="macaroon"),
    )

    assert gateway._namespace == "charm"
    assert gateway._client is not None


@pytest.mark.slow
def test_ubuntu_one_login_with_convenience_method(
    charmhub_login_url,
    charmhub_base_url,
    staging_sso_credentials,
):
    """Test the convenience login_with() method that does everything in one call.

    This demonstrates the simplest usage pattern for the UbuntuOneLogin class.
    Requires internet access and valid Charmhub credentials.
    """
    email, password = staging_sso_credentials

    # Perform a real login
    test_app_name = "ubuntu-one-login-convenience-test"
    # We need to use the netloc as the host for Auth, consistent with how
    # UbuntuOneLogin does it.
    host = urlparse(charmhub_base_url).netloc

    root, discharged = UbuntuOneLogin.login_with(
        email,
        password,
        login_url=charmhub_login_url,
        api_base_url=charmhub_base_url,
        application_name=test_app_name,
    )
    assert root is not None
    assert discharged is not None

    # Use with PublisherGateway
    # We use UbuntuOneAuth which handles the exchange internally using the
    # saved root/discharge macaroon pair.
    u1_auth = auth.Auth(
        application_name=test_app_name,
        host=host,
        file_fallback=True,
    )

    gateway = publisher.PublisherGateway(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=u1_auth,
        httpx_auth=UbuntuOneAuth(auth=u1_auth, api_base_url=charmhub_base_url),
    )
    user_info = gateway.whoami()
    assert user_info["account"]["email"] == email

    # Clean up keyring entry
    u1_auth.del_credentials()
