# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
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
"""Unit tests for the publisher gateway."""

from unittest import mock

import httpx
import pytest
from craft_store import errors, publishergateway


@pytest.fixture
def mock_httpx_client():
    return mock.Mock(spec=httpx.Client)


@pytest.fixture
def publisher_gateway(mock_httpx_client):
    gw = publishergateway.PublisherGateway("http://localhost", "charm", mock.Mock())
    gw._client = mock_httpx_client
    return gw


@pytest.mark.parametrize("response", [httpx.Response(status_code=204)])
def test_check_error_on_success(response: httpx.Response):
    assert publishergateway.PublisherGateway._check_error(response) is None


@pytest.mark.parametrize(
    ("response", "match"),
    [
        pytest.param(
            httpx.Response(503, text="help!"),
            r"Invalid response from server \(503\)",
            id="really-bad",
        ),
        pytest.param(
            httpx.Response(
                503,
                json={"error-list": [{"code": "whelp", "message": "we done goofed"}]},
            ),
            r"Store had an error \(503\): we done goofed",
            id="server-error",
        ),
        pytest.param(
            httpx.Response(
                400,
                json={"error-list": [{"code": "whelp", "message": "you messed up"}]},
            ),
            r"Error 400 returned from store: you messed up",
            id="client-error",
        ),
        pytest.param(
            httpx.Response(
                418,
                json={
                    "error-list": [
                        {"code": "whelp", "message": "I am a teapot"},
                        {
                            "code": "bad",
                            "message": "Why would you ask me for a coffee?",
                        },
                    ]
                },
            ),
            r"Error 418 returned from store. See log for details",
            id="multiple-client-errors",
        ),
    ],
)
def test_check_error(response: httpx.Response, match):
    with pytest.raises(errors.CraftStoreError, match=match):
        publishergateway.PublisherGateway._check_error(response)


def test_get_package_metadata(
    mock_httpx_client: mock.Mock, publisher_gateway: publishergateway.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200, json={"metadata": {"meta": "data"}}
    )

    assert publisher_gateway.get_package_metadata("my-package") == {"meta": "data"}

    mock_httpx_client.get.assert_called_once_with(url="/v1/charm/my-package")


@pytest.mark.parametrize(
    ("tracks", "match"),
    [
        ([{"name": "-"}], ": -$"),
        (
            [{"name": "123456789012345678901234567890"}],
            ": 123456789012345678901234567890$",
        ),
        ([{"name": "-"}, {"name": "_!"}], ": -, _!$"),
    ],
)
def test_create_tracks_validation(
    publisher_gateway: publishergateway.PublisherGateway,
    tracks,
    match,
):
    with pytest.raises(ValueError, match=match):
        publisher_gateway.create_tracks("my-name", *tracks)


def test_create_tracks_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publishergateway.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"num-tracks-created": 0}
    )

    assert publisher_gateway.create_tracks("my-name") == 0
