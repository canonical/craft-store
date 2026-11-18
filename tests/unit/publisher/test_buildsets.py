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

from typing import Any
from unittest import mock

import httpx
import pytest
from craft_store import errors
from craft_store.models import Plane
from craft_store.publisher import (
    Buildset,
    PublisherGateway,
    SourceStoreOperationStatus,
)

from .conftest import dict_with_optional_plane


def fake_package(
    *,
    name: str,
    package_type: str = "craft-type",
    package_id: str = "package-id-1",
    commit_hash: str = "craft-commit-hash",
    craft_version: str = "0.1",
    craft_track: str = "latest",
    craft_risk: str = "edge",
    craft_branch: str | None = None,
) -> dict[str, Any]:
    craft_channel_name = f"{craft_track}/{craft_risk}" + (
        f"/{craft_branch}" if craft_branch is not None else ""
    )
    return {
        "type": package_type,
        "name": name,
        "id": package_id,
        "commit-hash": commit_hash,
        "craft-version": craft_version,
        "craft-channel": {
            "name": craft_channel_name,
            "track": craft_track,
            "risk": craft_risk,
            "branch": craft_branch,
        },
    }


def fake_binary_release(
    *,
    track: str = "latest",
    risk: str = "edge",
    branch: str | None = None,
    revision: int = 1,
) -> dict[str, Any]:
    channel_name = f"{track}/{risk}" + (f"/{branch}" if branch is not None else "")
    return {
        "channel": {
            "name": channel_name,
            "track": track,
            "risk": risk,
            "branch": branch,
        },
        "revision": revision,
    }


def fake_build(
    *,
    build_id: str = "build-1",
    binary_release: dict[str, Any] | dict[None, None] | None = None,
    platform: dict[str, Any] | None = None,
    logs_url: str | None = "https://fake.logs.url.localhost",
    status: str = "succeeded",
    error_list: list[dict[str, str]] | None = None,
    created_at: str = "2024-11-19T10:12:09.391881+00:00",
    completed_at: str | None = "2024-11-19T10:19:54.016283+00:00",
) -> dict[str, Any]:
    if binary_release is None:
        binary_release = fake_binary_release()
    platform = platform or {
        "name": "ubuntu",
        "channel": "22.04",
        "architectures": ["amd64"],
    }
    errors = error_list or []
    return {
        "id": build_id,
        "binary-release": binary_release,
        "platform": platform,
        "logs": {"launchpad-build-url": logs_url},
        "status": status,
        "error-list": errors,
        "created-at": created_at,
        "completed-at": completed_at,
    }


def fake_buildset_response(
    *,
    buildset_id: str = "test-buildset-1",
    package: dict[str, Any] | None = None,
    platforms: list[dict[str, Any]] | None = None,
    triggers: list[dict[str, str]] | None = None,
    builds: list[dict[str, Any]] | None = None,
    created_at: str = "2024-11-19T10:12:09.375524",
) -> dict[str, Any]:
    package = package or fake_package(name="test-package")
    platforms = platforms or [
        {"name": "ubuntu", "channel": "22.04", "architectures": ["amd64"]}
    ]
    triggers = triggers or [{"type": "commit"}]
    builds = builds or [fake_build()]
    return {
        "id": buildset_id,
        "package": package,
        "platforms": platforms,
        "triggers": triggers,
        "builds": builds,
        "created-at": created_at,
    }


@pytest.fixture
def buildsets_endpoint() -> str:
    return "/v1/craft/buildsets"


@pytest.mark.parametrize(
    "extra_params",
    [
        pytest.param({}, id="no-params"),
        pytest.param({"channel": "latest/edge/test"}, id="channel_filter"),
        pytest.param({"commit_hash": "some-specific-commit-hash"}, id="commit_filter"),
        pytest.param({"buildset_id": "buildset-3"}, id="buildset_filter"),
        pytest.param({"status": SourceStoreOperationStatus.FAILED}, id="status_filter"),
        pytest.param(
            {
                "channel": "latest/edge/test",
                "commit_hash": "some-specific-commit-hash",
            },
            id="channel_and_commit_filters",
        ),
    ],
)
def test_get_buildsets(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    default_plane: Plane | None,
    extra_params: dict[str, Any],
    buildsets_endpoint: str,
) -> None:
    test_package_name = "test-package"
    mock_httpx_client.get.return_value = httpx.Response(
        httpx.codes.OK,
        json={"buildsets": [fake_buildset_response()]},
    )

    additional_filters = {k.replace("_", "-"): v for k, v in extra_params.items()}

    buildsets = craft_publisher_gateway.get_buildsets(
        package_name=test_package_name,
        **extra_params,
    )

    assert isinstance(buildsets[0], Buildset), "Incorrect API return type"

    mock_httpx_client.get.assert_called_with(
        buildsets_endpoint,
        params=dict_with_optional_plane(
            {
                "package": f"{craft_publisher_gateway._namespace}/{test_package_name}",
            }
            | additional_filters,
            default_plane,
        ),
    )


@pytest.mark.parametrize(
    "build_override",
    [
        pytest.param({"binary_release": {}}, id="without-binary-release"),
        pytest.param({"logs_url": None}, id="without-logs"),
    ],
)
def test_get_buildset_with_modified_build(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    default_plane: Plane | None,
    buildsets_endpoint: str,
    build_override: dict[str, Any],
) -> None:
    test_package_name = "test-package"
    build = fake_build(**build_override)
    buildsets = [fake_buildset_response(), fake_buildset_response(builds=[build])]
    mock_httpx_client.get.return_value = httpx.Response(
        httpx.codes.OK,
        json={"buildsets": buildsets},
    )

    package = f"{craft_publisher_gateway._namespace}/{test_package_name}"

    returned_buildsets = craft_publisher_gateway.get_buildsets(
        package_name=test_package_name,
    )
    assert isinstance(returned_buildsets[0], Buildset), "Incorrect API return type"

    mock_httpx_client.get.assert_called_with(
        buildsets_endpoint,
        params=dict_with_optional_plane(
            {
                "package": package,
            },
            default_plane,
        ),
    )


def test_get_buildsets_handles_error_from_store(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    invalid_store_response: httpx.Response,
    default_plane: Plane | None,
    buildsets_endpoint: str,
) -> None:
    test_package_name = "test-package"
    mock_httpx_client.get.return_value = invalid_store_response
    with pytest.raises(errors.CraftStoreError):
        _ = craft_publisher_gateway.get_buildsets(package_name=test_package_name)

    test_package = f"{craft_publisher_gateway._namespace}/{test_package_name}"

    mock_httpx_client.get.assert_called_with(
        buildsets_endpoint,
        params=dict_with_optional_plane(
            {
                "package": test_package,
            },
            default_plane,
        ),
    )


def test_get_buildsets_incorrect_response(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    default_plane: Plane | None,
    buildsets_endpoint: str,
) -> None:
    test_package_name = "test-package"
    mock_httpx_client.get.return_value = httpx.Response(
        httpx.codes.OK, json={"invalid-response": "dict"}
    )
    with pytest.raises(errors.InvalidResponseError):
        _ = craft_publisher_gateway.get_buildsets(package_name=test_package_name)
    test_package = f"{craft_publisher_gateway._namespace}/{test_package_name}"

    mock_httpx_client.get.assert_called_with(
        buildsets_endpoint,
        params=dict_with_optional_plane(
            {
                "package": test_package,
            },
            default_plane,
        ),
    )


def test_create_buildset(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    default_plane: Plane | None,
    buildsets_endpoint: str,
) -> None:
    test_package_name = "test-package"
    test_channel = "latest/edge"
    mock_httpx_client.post.return_value = httpx.Response(
        httpx.codes.OK,
        json={"buildsets": [{"id": "triggered-buildset-id"}]},
    )

    buildset_ids = craft_publisher_gateway.create_buildset(
        package_name=test_package_name,
        channel=test_channel,
    )

    assert buildset_ids[0].entity_id == "triggered-buildset-id"

    mock_httpx_client.post.assert_called_with(
        buildsets_endpoint,
        json=dict_with_optional_plane(
            {
                "action": "build",
                "channel": test_channel,
                "package-name": test_package_name,
                "package-type": craft_publisher_gateway._namespace,
            },
            default_plane,
        ),
    )


def test_trigger_buildset_error_from_store(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    invalid_store_response: httpx.Response,
    default_plane: Plane | None,
    buildsets_endpoint: str,
) -> None:
    test_package_name = "test-package"
    test_channel = "latest/edge"
    mock_httpx_client.post.return_value = invalid_store_response

    with pytest.raises(errors.CraftStoreError):
        _ = craft_publisher_gateway.create_buildset(
            package_name=test_package_name,
            channel=test_channel,
        )

    mock_httpx_client.post.assert_called_with(
        buildsets_endpoint,
        json=dict_with_optional_plane(
            {
                "action": "build",
                "channel": test_channel,
                "package-name": test_package_name,
                "package-type": craft_publisher_gateway._namespace,
            },
            default_plane,
        ),
    )
