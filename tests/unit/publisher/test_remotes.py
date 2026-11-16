# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2025 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Tests for manipulating remotes using PublisherGateway API."""

from unittest import mock

import httpx
import pytest
from craft_store import errors
from craft_store.errors import (
    MissingUrlForExternalRemoteError,
    UrlProvidedForManagedRemoteError,
)
from craft_store.models import Plane
from craft_store.publisher import CraftPublisherGateway

from .conftest import dict_with_optional_plane


def _fake_remote_response(
    remote_type: str = "external",
    name: str = "origin",
    package_type: str = "bin",
    package_name: str = "origin-test",
    package_id: str = "package-1",
    plane: Plane | None = None,
    url: str | None = None,
) -> dict[str, str]:
    if url is None:
        url = f"git+ssh://test@localhost/{package_name}-repo"

    return dict_with_optional_plane(
        {
            "type": remote_type,
            "name": name,
            "package-type": package_type,
            "package-name": package_name,
            "package-id": package_id,
            "url": url,
        },
        plane,
    )


@pytest.fixture
def remotes_endpoint() -> str:
    return "/v1/craft/remotes"


def test_get_remotes(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane | None,
    remotes_endpoint: str,
) -> None:
    """Test getting remotes for given package."""
    package_name = "test-package-1"

    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "remotes": [
                _fake_remote_response(package_name=package_name, plane=default_plane),
            ]
        },
    )

    remotes = craft_publisher_gateway.get_remotes(package_name)

    assert len(remotes) == 1, "Single list item should be returned."
    mock_httpx_client.get.assert_called_with(
        remotes_endpoint,
        params=dict_with_optional_plane(
            {
                "package": f"{craft_publisher_gateway._namespace}/{package_name}",
            },
            default_plane,
        ),
    )


def test_get_remotes_invalid_response(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    invalid_store_response: httpx.Response,
    default_plane: Plane,
) -> None:
    """Test getting remotes raises CraftStoreError."""
    mock_httpx_client.get.return_value = invalid_store_response
    with pytest.raises(errors.CraftStoreError):
        _ = craft_publisher_gateway.get_remotes("test-package")


def test_get_remotes_malformed_response(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane,
) -> None:
    """Test getting remotes raises CraftStoreError."""
    package_name = "test-package"

    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={"incorrect_response": []},
    )

    with pytest.raises(errors.InvalidResponseError):
        _ = craft_publisher_gateway.get_remotes(package_name)


def test_get_remotes_missing_field(
    craft_publisher_gateway: CraftPublisherGateway, mock_httpx_client: mock.Mock
) -> None:
    """Test getting remotes raises CraftStoreError."""
    package_name = "malformed-package"
    malformed_remote = _fake_remote_response(package_name)
    malformed_remote.pop("name")

    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={"remotes": [malformed_remote]},
    )

    with pytest.raises(errors.CraftStoreError):
        _ = craft_publisher_gateway.get_remotes(package_name)


@pytest.mark.parametrize(
    "action",
    ["setup", "remove"],
    ids=lambda p: f"action_{p}",
)
@pytest.mark.parametrize(
    "remote_type",
    ["external", "managed"],
    ids=lambda p: f"remote_type_{p}",
)
@pytest.mark.parametrize(
    "access_token",
    [None, "access-user:super-secret-token"],
    ids=["no_acess_token", "with_access_token"],
)
def test_update_remote(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane,
    remote_type,
    action,
    remotes_endpoint: str,
    access_token: str | None,
) -> None:
    package_name = "test-package"
    remote_name = f"{remote_type}-remote"
    fake_remote_url = "https://fake.external-remote.localhost"

    extra_request_params = {}
    extra_args = {}
    if action == "setup" and remote_type == "external":
        extra_args["url"] = fake_remote_url
        extra_request_params["url"] = fake_remote_url

    if access_token:
        extra_args["access_token"] = access_token
        extra_request_params["access-token"] = access_token

    mock_httpx_client.post.return_value = httpx.Response(
        httpx.codes.CREATED,
        json=_fake_remote_response(
            name=remote_name,
            remote_type=remote_type,
            package_name=package_name,
            url=fake_remote_url,
        ),
    )
    remote = craft_publisher_gateway.update_remote(
        action=action,
        package_name=package_name,
        remote_name=remote_name,
        remote_type=remote_type,
        **extra_args,  # ty: ignore[invalid-argument-type]
    )

    assert remote.name == remote_name, "Incorrect remote name"
    assert remote.remote_type == remote_type, "Incorrect remote type"

    mock_httpx_client.post.assert_called_with(
        remotes_endpoint,
        json=dict_with_optional_plane(
            {
                "action": action,
                "name": remote_name,
                "type": remote_type,
                "package-name": package_name,
                "package-type": craft_publisher_gateway._namespace,
            }
            | extra_request_params,
            default_plane,
        ),
    )


def test_cannot_setup_external_remote_without_url(
    craft_publisher_gateway: CraftPublisherGateway, mock_httpx_client: mock.Mock
) -> None:
    package_name = "test-package"

    with pytest.raises(MissingUrlForExternalRemoteError):
        craft_publisher_gateway.update_remote(
            action="setup",
            package_name=package_name,
            remote_name="incorrect-external-remote",
            remote_type="external",
        )


def test_cannot_setup_managed_remote_with_url(
    craft_publisher_gateway: CraftPublisherGateway, mock_httpx_client: mock.Mock
) -> None:
    package_name = "test-package"

    with pytest.raises(UrlProvidedForManagedRemoteError):
        craft_publisher_gateway.update_remote(
            action="setup",
            package_name=package_name,
            remote_name="incorrect-managed-remote",
            remote_type="managed",
            url="https://incorrect.managed.url.localhost",
        )


def test_update_managed_returns_incorrect_respose(
    craft_publisher_gateway: CraftPublisherGateway, mock_httpx_client: mock.Mock
) -> None:
    package_name = "test-package"

    mock_httpx_client.post.return_value = httpx.Response(
        httpx.codes.CREATED,
        json={"incorrect-response": "some"},
    )

    with pytest.raises(errors.CraftStoreError):
        craft_publisher_gateway.update_remote(
            action="setup",
            package_name=package_name,
            remote_name="malformed-remote-response",
            remote_type="external",
            url="https://managed.url.localhost",
        )
