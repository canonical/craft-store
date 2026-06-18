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
import time
from urllib.parse import urlparse

import keyring
import pytest
from craft_store import DeveloperTokenAuth, auth, errors, publisher
from craft_store.auth import MemoryKeyring
from craft_store.login import UbuntuOneLogin


@pytest.fixture(autouse=True)
def _test_keyring():
    """In-memory keyring backend for testing."""
    current_keyring = keyring.get_keyring()
    keyring.set_keyring(MemoryKeyring())
    yield
    keyring.set_keyring(current_keyring)


@pytest.fixture
def charmhub_login_url() -> str:
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
    charmhub_login_url: str,
    charmhub_base_url: str,
) -> None:
    """Smoke test for UbuntuOneLogin and PublisherGateway connectivity."""
    login_client = UbuntuOneLogin(
        base_url=charmhub_base_url,
        login_url=charmhub_login_url,
    )

    macaroon = login_client._get_macaroon(
        permissions=["package-view"],
    )

    assert macaroon is not None
    assert macaroon.serialize() is not None

    test_auth = auth.Auth(
        application_name="ubuntu-one-login-smoke-test",
        host=urlparse(charmhub_base_url).netloc,
        file_fallback=True,
    )
    gateway = publisher.PublisherGateway(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=DeveloperTokenAuth(auth=test_auth, auth_type="macaroon"),
    )

    assert gateway._namespace == "charm"
    assert gateway._client is not None


@pytest.mark.slow
@pytest.mark.timeout(30)
def test_ubuntu_one_login_with_convenience_method(
    charmhub_login_url: str,
    charmhub_base_url: str,
    staging_sso_credentials,
) -> None:
    """Test the convenience login_with() method that does everything in one call."""
    email, password = staging_sso_credentials
    test_app_name = "ubuntu-one-login-convenience-test"
    host = urlparse(charmhub_base_url).netloc

    root, discharged = UbuntuOneLogin.login_with(
        email,
        password,
        login_url=charmhub_login_url,
        base_url=charmhub_base_url,
        application_name=test_app_name,
        otp=None,
    )
    assert root is not None
    assert discharged is not None

    u1_auth = auth.Auth(
        application_name=test_app_name,
        host=host,
        file_fallback=True,
    )

    gateway = publisher.PublisherGateway.with_ubuntu_one(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=u1_auth,
    )
    user_info = gateway.whoami()
    assert user_info["account"]["email"] == email

    u1_auth.del_credentials()


@pytest.mark.slow
@pytest.mark.timeout(30)
def test_ubuntu_one_login_with_keyring_reuse_real(
    charmhub_login_url: str,
    charmhub_base_url: str,
    staging_sso_credentials,
) -> None:
    """Test that credentials can be cached and reused from the keyring."""
    email, password = staging_sso_credentials
    test_app_name = "ubuntu-one-login-keyring-reuse-real-test"
    host = urlparse(charmhub_base_url).netloc

    _perform_login_real(
        email, password, charmhub_login_url, charmhub_base_url, test_app_name
    )

    user_info, test_auth = _retrieve_from_keyring_real(
        charmhub_base_url, test_app_name, host
    )

    assert user_info["account"]["email"] == email

    test_auth.del_credentials()


def _perform_login_real(
    email: str,
    password: str,
    charmhub_login_url: str,
    charmhub_base_url: str,
    test_app_name: str,
) -> None:
    """Perform a real login with fresh objects."""
    try:
        root, discharged = UbuntuOneLogin.login_with(
            email,
            password,
            base_url=charmhub_base_url,
            login_url=charmhub_login_url,
            application_name=test_app_name,
            otp=None,
        )
    except Exception as exc:
        if "otp" in str(exc).lower() or "two.factor" in str(exc).lower():
            pytest.skip(f"OTP required: {exc}")
        raise

    assert root is not None
    assert discharged is not None


def _retrieve_from_keyring_real(
    charmhub_base_url: str,
    test_app_name: str,
    host: str,
) -> tuple[dict, auth.Auth]:
    """Retrieve credentials from the keyring with fresh objects."""
    new_auth = auth.Auth(
        application_name=test_app_name,
        host=host,
        file_fallback=True,
    )
    new_gateway = publisher.PublisherGateway.with_ubuntu_one(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=new_auth,
    )
    user_info = new_gateway.whoami()
    return user_info, new_auth


@pytest.mark.slow
@pytest.mark.timeout(30)
def test_ubuntu_one_login_with_expired_ttl_real(
    charmhub_login_url: str,
    charmhub_base_url: str,
    staging_sso_credentials,
) -> None:
    """Login with real credentials, let the token expire, and assert the error."""
    email, password = staging_sso_credentials
    test_app_name = "ubuntu-one-login-expired-ttl-test"
    host = urlparse(charmhub_base_url).netloc

    UbuntuOneLogin.login_with(
        email,
        password,
        base_url=charmhub_base_url,
        login_url=charmhub_login_url,
        application_name=test_app_name,
        otp=None,
        ttl=10,  # Shortest allowed TTL
    )

    local_auth = auth.Auth(
        application_name=test_app_name,
        host=host,
        file_fallback=True,
    )
    gateway = publisher.PublisherGateway.with_ubuntu_one(
        base_url=charmhub_base_url,
        namespace="charm",
        auth=local_auth,
    )

    user_info = gateway.whoami()
    assert user_info["account"]["email"] == email

    time.sleep(10)  # Expire the macaroon

    with pytest.raises(errors.CraftStoreError, match="Error 401 returned from store."):
        gateway.whoami()


@pytest.mark.slow
@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    ("ttl", "message"),
    [
        (3, "3 is less than the minimum of 10 at /ttl"),
        (10**9, "1000000000 is greater than the maximum of 31536000 at /ttl"),
    ],
)
def test_ubuntu_one_login_with_invalid_ttl_real(
    charmhub_login_url: str,
    charmhub_base_url: str,
    staging_sso_credentials,
    ttl: int,
    message: str,
) -> None:
    """Login with a TTL that the server rejects and assert the error."""
    email, password = staging_sso_credentials
    test_app_name = f"ubuntu-one-login-invalid-ttl-{ttl}-test"

    with pytest.raises(errors.InvalidRequestError, match=message) as exc_info:
        UbuntuOneLogin.login_with(
            email,
            password,
            base_url=charmhub_base_url,
            login_url=charmhub_login_url,
            application_name=test_app_name,
            otp=None,
            ttl=ttl,
        )

    assert exc_info.value.details == "api-error"
