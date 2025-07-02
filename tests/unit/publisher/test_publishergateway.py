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

import logging
import textwrap
from typing import Any
from unittest import mock

import httpx
import pydantic
import pytest
import pytest_check
from craft_store import errors, publisher
from craft_store.errors import StoreErrorList
from craft_store.publisher import RegisteredName, ReleaseResult, Revision
from craft_store.publisher._response import ReleasedResourceRevision


@pytest.fixture
def mock_httpx_client():
    return mock.Mock(spec=httpx.Client)


@pytest.fixture
def publisher_gateway(mock_httpx_client):
    gw = publisher.PublisherGateway("http://localhost", "charm", mock.Mock())
    gw._client = mock_httpx_client
    return gw


@pytest.mark.parametrize("response", [httpx.Response(status_code=204)])
def test_check_error_on_success(response: httpx.Response):
    publisher.PublisherGateway._check_error(response)


@pytest.mark.parametrize(
    ("response", "match", "has_error_list"),
    [
        pytest.param(
            httpx.Response(503, text="help!"),
            r"Store returned an invalid response \(status: 503\)",
            False,
            id="really-bad",
        ),
        pytest.param(
            httpx.Response(
                503,
                json={"error-list": [{"code": "whelp", "message": "we done goofed"}]},
            ),
            r"Store had an error \(503\): we done goofed",
            True,
            id="server-error",
        ),
        pytest.param(
            httpx.Response(
                400,
                json={"error-list": [{"code": "whelp", "message": "you messed up"}]},
            ),
            r"Error 400 returned from store: you messed up",
            True,
            id="client-error",
        ),
        pytest.param(
            httpx.Response(
                418,
                json={
                    "error-list": [
                        {"code": "good", "message": "I am a teapot"},
                        {
                            "code": "bad",
                            "message": "Why would you ask me for coffee?",
                        },
                    ]
                },
            ),
            textwrap.dedent(
                """\
                Error 418 returned from store.
                - good: I am a teapot
                - bad: Why would you ask me for coffee?"""
            ),
            True,
            id="multiple-client-errors",
        ),
    ],
)
def test_check_error(response: httpx.Response, match, has_error_list, caplog):
    caplog.set_level(logging.DEBUG)

    with pytest.raises(errors.CraftStoreError, match=match) as exc:
        publisher.PublisherGateway._check_error(response)

    assert exc.value.details is None

    if has_error_list:
        error_list = response.json().get("error-list", [])
        expected_log = f"Errors from the store:\n{StoreErrorList(error_list)}"
        assert expected_log in caplog.text


@pytest.mark.parametrize(
    "results",
    [
        [],
        [
            {
                "id": "abc",
                "private": False,
                "publisher": {"id": "def"},
                "status": "there",
                "store": "yep",
                "type": "charm",
            }
        ],
    ],
)
def test_list_registered_names_success(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    results: list[dict],
):
    mock_httpx_client.get.return_value = httpx.Response(200, json={"results": results})

    publisher_gateway.list_registered_names()


@pytest.mark.parametrize(
    ("response", "message"),
    [
        ({}, r"Store returned an invalid response \(status: 200\)"),
    ],
)
def test_list_registered_names_bad_response(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    response: Any,
    message: str,
):
    mock_httpx_client.get.return_value = httpx.Response(200, json=response)

    with pytest.raises(errors.InvalidResponseError, match=message):
        publisher_gateway.list_registered_names()


@pytest.mark.parametrize(
    ("response", "message"),
    [({"results": [{}]}, "validation errors for RegisteredNameModel")],
)
def test_list_registered_names_invalid_result(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    response: Any,
    message: str,
):
    mock_httpx_client.get.return_value = httpx.Response(200, json=response)

    with pytest.raises(pydantic.ValidationError, match=message):
        publisher_gateway.list_registered_names()


@pytest.mark.parametrize("entity_type", ["charm", "rock", "snap"])
@pytest.mark.parametrize("private", [True, False])
@pytest.mark.parametrize("team", ["my-team", None])
def test_register_name_success(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    entity_type: str,
    private: bool,
    team: str | None,
):
    mock_httpx_client.post.return_value = httpx.Response(200, json={"id": "abc"})

    publisher_gateway.register_name(
        "my-name", entity_type=entity_type, private=private, team=team
    )

    call = mock_httpx_client.post.mock_calls[0]
    json = call.kwargs["json"]

    pytest_check.equal(json["name"], "my-name")
    pytest_check.equal(json["private"], private)
    pytest_check.equal(json.get("team"), team)
    pytest_check.equal(json.get("type"), entity_type)


def test_register_name_error(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
):
    mock_httpx_client.post.return_value = httpx.Response(200, json={})

    with pytest.raises(errors.InvalidResponseError):
        publisher_gateway.register_name("my-name", entity_type="snazzy")


def test_get_package_metadata(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    fake_registered_name_dict: dict[str, Any],
    fake_registered_name_model: RegisteredName,
):
    mock_httpx_client.get.return_value = httpx.Response(
        200, json={"metadata": fake_registered_name_dict}
    )

    actual = publisher_gateway.get_package_metadata("my-package")

    assert actual == fake_registered_name_model

    mock_httpx_client.get.assert_called_once_with(url="/v1/charm/my-package")


def test_unregister_name_success(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
):
    mock_httpx_client.delete.return_value = httpx.Response(
        200, json={"package-id": "baleted!"}
    )

    publisher_gateway.unregister_name("my-name")


def test_unregister_name_bad_response(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
):
    mock_httpx_client.delete.return_value = httpx.Response(200, json={})

    with pytest.raises(errors.InvalidResponseError) as exc_info:
        publisher_gateway.unregister_name("my-name")

    assert exc_info.value.details == "Missing JSON keys: {'package-id'}"


@pytest.mark.parametrize(
    ("status_code", "json", "error_code"),
    [
        (
            404,
            {
                "error-list": [
                    {
                        "code": "resource-not-found",
                        "message": "Name my-name not found in the charm namespace",
                    }
                ]
            },
            "resource-not-found",
        ),
        (
            403,
            {
                "error-list": [
                    {
                        "code": "forbidden",
                        "message": "Cannot unregister a package with existing revisions",
                    }
                ]
            },
            "forbidden",
        ),
        (
            401,
            {
                "error-list": [
                    {
                        "code": "permission-required",
                        "message": "Charms can only be unregistered by their publisher",
                    }
                ]
            },
            "permission-required",
        ),
    ],
)
def test_unregister_name_client_errors(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    status_code: int,
    json: dict,
    error_code: str,
    caplog,
):
    caplog.set_level(logging.DEBUG)
    mock_httpx_client.delete.return_value = httpx.Response(status_code, json=json)

    with pytest.raises(errors.CraftStoreError):
        publisher_gateway.unregister_name("my-name")

    assert error_code in caplog.text


@pytest.mark.parametrize(
    ("json_values"),
    [
        pytest.param([], id="empty"),
        pytest.param(
            [
                {
                    "created-at": "2000-01-01T00:00:00Z",
                    "revision": 1,
                    "sha3-384": "734e1ec20ce19747101614c1cd924b2745b56d291d53973304a5e6390b9101b78fa19f966ffed86c9de570a5e2c163dc",
                    "size": 0,
                    "status": "empty",
                    "version": "1",
                },
                {
                    "created-at": "2000-01-01T00:00:00Z",
                    "created-by": "someone",
                    "errors": [{"code": "0", "message": "Oops!"}],
                    "revision": 2,
                    "sha3-384": "734e1ec20ce19747101614c1cd924b2745b56d291d53973304a5e6390b9101b78fa19f966ffed86c9de570a5e2c163dc",
                    "size": 124546586765432456876764,
                    "status": "bad",
                    "version": "versiony",
                },
            ],
            id="has-values",
        ),
    ],
)
def test_list_revisions_success(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    json_values,
):
    mock_httpx_client.get.return_value = httpx.Response(
        200, json={"revisions": json_values}
    )
    result = publisher_gateway.list_revisions("my-name")

    mock_httpx_client.get.assert_called_once_with(
        "/v1/charm/my-name/revisions", params={}
    )

    assert result == [Revision.unmarshal(rev) for rev in json_values]


@pytest.mark.parametrize(
    ("fields", "expected_fields"),
    [
        ([], ""),
        (["size", "status"], "size,status"),
        ({"commit-id"}, "commit-id"),
    ],
)
@pytest.mark.parametrize("include_craft_yaml", [True, False])
@pytest.mark.parametrize("revision", [None, 123])
def test_list_revisions_parameters(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    fields: list[str] | None,
    expected_fields: str | None,
    include_craft_yaml: bool,
    revision: int | None,
):
    mock_httpx_client.get.return_value = httpx.Response(200, json={"revisions": []})
    include_str = str(include_craft_yaml).lower()

    publisher_gateway.list_revisions(
        "my-name",
        fields=fields,
        include_craft_yaml=include_craft_yaml,
        revision=revision,
    )

    call = mock_httpx_client.get.mock_calls[0]

    assert call.args[0] == "/v1/charm/my-name/revisions"
    actual_params = call.kwargs["params"]

    assert actual_params.get("fields") == expected_fields
    assert actual_params.get("include-craft-yaml", "false") == include_str
    assert actual_params.get("revision") == (str(revision) if revision else None)


@pytest.mark.parametrize(
    ("requests", "expected"),
    [
        pytest.param([], [], id="empty"),
        pytest.param(
            [{"channel": "latest/edge", "revision": 123}],
            [ReleaseResult(channel="latest/edge", revision=123)],
        ),
        pytest.param(
            [
                {
                    "channel": "latest/edge",
                    "revision": 123,
                    "resources": [{"name": "my-resource", "revision": 456}],
                }
            ],
            [
                ReleaseResult(
                    channel="latest/edge",
                    revision=123,
                    resources=[
                        ReleasedResourceRevision(name="my-resource", revision=456)
                    ],
                )
            ],
            id="with_resource",
        ),
    ],
)
def test_release(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    requests,
    expected,
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"released": requests}
    )

    actual = publisher_gateway.release("my-name", requests)

    assert actual == expected


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
    publisher_gateway: publisher.PublisherGateway,
    tracks,
    match,
):
    with pytest.raises(ValueError, match=match):
        publisher_gateway.create_tracks("my-name", *tracks)


def test_create_tracks_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"num-tracks-created": 0}
    )

    assert publisher_gateway.create_tracks("my-name") == 0
