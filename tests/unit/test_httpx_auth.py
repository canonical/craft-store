# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021,2024 Canonical Ltd.
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

from typing import Literal, cast

import httpx
import pytest
import pytest_httpx
import pytest_mock
from craft_store import CandidAuth, DeveloperTokenAuth, creds, errors
from craft_store.auth import Auth


@pytest.fixture
def candid_auth(mock_auth):
    return CandidAuth(
        auth=mock_auth,
    )


def test_candid_get_token_from_keyring(mock_auth, candid_auth):
    mock_auth.get_credentials.return_value = "{}"

    assert candid_auth.get_token_from_keyring() == "{}"


def test_candid_auth_flow(mock_auth, candid_auth):
    mock_auth.get_credentials.return_value = "{}"

    request = httpx.Request("GET", "http://localhost")

    next(candid_auth.auth_flow(request))

    assert request.headers["Authorization"] == "Macaroon {}"


@pytest.fixture
def dev_token_for_testing() -> str:
    return "test-dev-token"


@pytest.fixture(params=["bearer", "macaroon"], ids=lambda a: f"auth_{a}")
def auth_type(request: pytest.FixtureRequest) -> str:
    return cast(str, request.param)


@pytest.fixture
def developer_token_auth(
    dev_token_for_testing: str,
    auth_type: Literal["bearer", "macaroon"],
) -> DeveloperTokenAuth:
    auth = Auth(
        application_name="test-craft",
        host="test-host.localhost",
        ephemeral=True,
    )
    auth.set_credentials(
        creds.DeveloperToken(macaroon=dev_token_for_testing).model_dump_json()
    )
    return DeveloperTokenAuth(auth=auth, auth_type=auth_type)


def test_auth_flow_token_injection(
    dev_token_for_testing: str,
    developer_token_auth: DeveloperTokenAuth,
    auth_type: str,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """Check if header is correctly populated if token is available."""
    expected_headers = {}
    if auth_type == "bearer":
        expected_headers["Authorization"] = f"Bearer {dev_token_for_testing}"
    if auth_type == "macaroon":
        expected_headers["Authorization"] = f"Macaroon {dev_token_for_testing}"

    httpx_client = httpx.Client(auth=developer_token_auth)
    httpx_mock.add_response(
        method="GET",
        json="it's working",
        url="https://fake-testcraft-url.localhost",
        match_headers=expected_headers,
    )
    httpx_client.request("GET", "https://fake-testcraft-url.localhost")


def test_auth_if_token_unavailable() -> None:
    app_name = "testcraft"
    host = "test-host.localhost"
    auth = Auth(
        application_name=app_name,
        host=host,
        ephemeral=True,
    )
    developer_token_auth = DeveloperTokenAuth(auth=auth)
    httpx_client = httpx.Client(auth=developer_token_auth)

    with pytest.raises(
        errors.CredentialsUnavailable,
        match=f"No credentials found for {app_name!r} on {host!r}.",
    ):
        httpx_client.request("GET", "https://fake-testcraft-url.localhost")


def test_auth_if_token_unset(
    developer_token_auth: DeveloperTokenAuth,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # do not set token that is available in keyring
    mocker.patch.object(
        developer_token_auth, "get_token_from_keyring", return_value=None
    )
    client = httpx.Client(auth=developer_token_auth)
    with pytest.raises(
        errors.AuthTokenUnavailableError,
        match="Token is not available",
    ):
        client.request("GET", "https://fake-testcraft-url.localhost")
