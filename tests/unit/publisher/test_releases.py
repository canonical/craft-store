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
"""Test for list_releases API."""

import json
import pathlib
from typing import Any, cast
from unittest import mock

import httpx
import pytest
from craft_store import errors
from craft_store.publisher import CraftPublisherGateway


@pytest.fixture
def package_name() -> str:
    return "test-package"


@pytest.fixture
def releases_endpoint(
    craft_publisher_gateway: CraftPublisherGateway, package_name: str
) -> str:
    return f"/v1/{craft_publisher_gateway._namespace}/{package_name}/releases"


@pytest.fixture
def fake_bin_releases(sourcestore_data_dir: pathlib.Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((sourcestore_data_dir / "status_bin_response.json").read_text()),
    )


@pytest.fixture
def fake_rock_releases(sourcestore_data_dir: pathlib.Path) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((sourcestore_data_dir / "status_rock_response.json").read_text()),
    )


def test_list_rock_releases(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: CraftPublisherGateway,
    releases_endpoint: str,
    fake_rock_releases: dict[str, Any],
    package_name: str,
) -> None:
    mock_httpx_client.get.return_value = httpx.Response(
        httpx.codes.OK,
        json=fake_rock_releases,
    )

    releases = craft_publisher_gateway.list_releases(package_name)

    assert releases.revisions, "There should be at least one revision."

    mock_httpx_client.get.assert_called_with(releases_endpoint)


def test_list_bin_releases(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: CraftPublisherGateway,
    releases_endpoint: str,
    fake_bin_releases: dict[str, Any],
    package_name: str,
) -> None:
    mock_httpx_client.get.return_value = httpx.Response(
        httpx.codes.OK,
        json=fake_bin_releases,
    )

    releases = craft_publisher_gateway.list_releases(package_name)

    assert releases.revisions, "There should be at least one revision."

    mock_httpx_client.get.assert_called_with(
        releases_endpoint,
    )


def test_list_releases_error_response(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: CraftPublisherGateway,
    releases_endpoint: str,
    invalid_store_response: httpx.Response,
    package_name: str,
) -> None:
    mock_httpx_client.get.return_value = invalid_store_response
    with pytest.raises(errors.CraftStoreError):
        craft_publisher_gateway.list_releases(package_name)

    mock_httpx_client.get.assert_called_with(releases_endpoint)
