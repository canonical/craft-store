# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
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
"""Fixtures for publisher gateway tests."""

import pathlib
from typing import Any, cast
from unittest import mock

import httpx
import pytest
from craft_store.models import Plane
from craft_store.publisher import CraftPublisherGateway


def dict_with_optional_plane(
    data: dict[str, Any], plane: Plane | None
) -> dict[str, Any]:
    """Attach plane parameters to dict if plane is provided."""
    if plane is not None:
        data["plane-name"] = plane.plane_name
        data["domain-name"] = plane.domain_name
    return data


@pytest.fixture
def sourcestore_data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parents[2] / "data" / "sourcestore"


@pytest.fixture(params=["craft/public", None], ids=["public_plane", "no_plane"])
def default_plane(request: pytest.FixtureRequest) -> Plane | None:
    if plane := request.param:
        plane = Plane.from_str(plane)
    return cast(Plane | None, plane)


@pytest.fixture
def mock_httpx_client() -> mock.Mock:
    return mock.Mock(spec=httpx.Client)


@pytest.fixture
def craft_publisher_gateway(
    mock_httpx_client: mock.Mock, default_plane: Plane | None, mock_auth: mock.Mock
) -> CraftPublisherGateway:
    gw_client = CraftPublisherGateway(
        "http://publisher_gw.localhost",
        "testcraft",
        mock_auth,
        plane=default_plane,
    )
    gw_client._client = mock_httpx_client
    return gw_client


@pytest.fixture(
    params=[
        pytest.param(
            httpx.Response(
                httpx.codes.SERVICE_UNAVAILABLE,
                text="Service Unavailable",
            ),
            id="bad-error-without-store-error",
        ),
        pytest.param(
            httpx.Response(
                httpx.codes.INTERNAL_SERVER_ERROR,
                json={
                    "error-list": [
                        {
                            "code": "server-error",
                            "message": "something bad happened",
                        }
                    ]
                },
            ),
            id="server-error",
        ),
        pytest.param(
            httpx.Response(
                httpx.codes.BAD_REQUEST,
                json={
                    "error-list": [
                        {
                            "code": "incorrect-data",
                            "message": "cannot proceed with sent data",
                        },
                    ]
                },
            ),
            id="bad-request",
        ),
    ],
)
def invalid_store_response(request: pytest.FixtureRequest) -> httpx.Response:
    return cast(httpx.Response, request.param)
