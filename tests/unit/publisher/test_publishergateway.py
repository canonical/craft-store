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
from craft_store.publisher import (
    ExchangeDashboardMacaroonsResponse,
    ExchangeMacaroonRequest,
    ExchangeMacaroonResponse,
    GetMacaroonResponse,
    MacaroonInfo,
    MacaroonRequest,
    MacaroonResponse,
    OciImageResourceBlobResponse,
    OciImageResourceUploadCredentialsResponse,
    OfflineExchangeMacaroonResponse,
    PushResourceRequest,
    PushResourceResponse,
    PushRevisionRequest,
    PushRevisionResponse,
    RegisteredName,
    ReleaseResult,
    ResourceRevisionsList,
    ResourceRevisionUpdateRequest,
    Revision,
    RevokeMacaroonResponse,
    UpdatePackageMetadataRequest,
    UpdatePackageMetadataResponse,
    UpdateResourceRevisionsResponse,
)
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


def test_get_macaroon_success_with_existing_macaroons(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "macaroons": [
                {
                    "description": "Test macaroon",
                    "session-id": "session-123",
                    "valid-since": "2024-01-01T00:00:00Z",
                    "valid-until": "2024-12-31T23:59:59Z",
                }
            ]
        },
    )

    result = publisher_gateway.get_macaroon()

    assert isinstance(result, GetMacaroonResponse)
    assert result.macaroons is not None
    assert len(result.macaroons) == 1
    assert result.macaroons[0].session_id == "session-123"
    mock_httpx_client.get.assert_called_once_with("/v1/tokens", params={})


def test_get_macaroon_success_with_bakery_macaroon(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200, json={"macaroon": "bakery-v2-macaroon"}
    )

    result = publisher_gateway.get_macaroon(include_inactive=True)

    assert isinstance(result, GetMacaroonResponse)
    assert result.macaroon == "bakery-v2-macaroon"
    mock_httpx_client.get.assert_called_once_with(
        "/v1/tokens", params={"include-inactive": "true"}
    )


def test_issue_macaroon_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"macaroon": "test-macaroon"}
    )

    request = MacaroonRequest(
        permissions=["package-upload"], description="Test client", ttl=3600
    )

    result = publisher_gateway.issue_macaroon(request)

    assert isinstance(result, MacaroonResponse)
    mock_httpx_client.post.assert_called_once_with(
        "/v1/tokens",
        json={
            "permissions": ["package-upload"],
            "description": "Test client",
            "ttl": 3600,
        },
    )


def test_exchange_macaroons_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"macaroon": "exchanged-macaroon"}
    )

    request = ExchangeMacaroonRequest(macaroon="discharged-macaroon")

    result = publisher_gateway.exchange_macaroons(request)

    assert isinstance(result, ExchangeMacaroonResponse)
    mock_httpx_client.post.assert_called_once_with(
        "/v1/tokens/exchange", json={"macaroon": "discharged-macaroon"}
    )


def test_exchange_dashboard_macaroons_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"macaroon": "developer-token"}
    )

    result = publisher_gateway.exchange_dashboard_macaroons("dashboard-sso-macaroons")

    assert isinstance(result, ExchangeDashboardMacaroonsResponse)
    assert result.macaroon == "developer-token"
    mock_httpx_client.post.assert_called_once_with(
        "/v1/tokens/dashboard/exchange",
        json={},
        headers={"Authorization": "dashboard-sso-macaroons"},
    )


def test_exchange_dashboard_macaroons_with_description_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"macaroon": "developer-token"}
    )

    result = publisher_gateway.exchange_dashboard_macaroons(
        "dashboard-sso-macaroons", description="My CLI Tool"
    )

    assert isinstance(result, ExchangeDashboardMacaroonsResponse)
    assert result.macaroon == "developer-token"
    mock_httpx_client.post.assert_called_once_with(
        "/v1/tokens/dashboard/exchange",
        json={"client-description": "My CLI Tool"},
        headers={"Authorization": "dashboard-sso-macaroons"},
    )


def test_offline_exchange_macaroon_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"macaroon": "offline-exchanged-macaroon"}
    )

    result = publisher_gateway.offline_exchange_macaroon("macaroon-to-exchange")

    assert isinstance(result, OfflineExchangeMacaroonResponse)
    assert result.macaroon == "offline-exchanged-macaroon"
    mock_httpx_client.post.assert_called_once_with(
        "/v1/tokens/offline/exchange", json={"macaroon": "macaroon-to-exchange"}
    )


def test_revoke_macaroon_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200,
        json={
            "macaroons": [
                {
                    "description": "Test macaroon",
                    "session-id": "session-456",
                    "valid-since": "2024-01-01T00:00:00Z",
                    "valid-until": "2024-12-31T23:59:59Z",
                    "revoked-at": "2024-06-01T10:00:00Z",
                    "revoked-by": "test-user",
                }
            ]
        },
    )

    result = publisher_gateway.revoke_macaroon("session-123")

    assert isinstance(result, RevokeMacaroonResponse)
    assert len(result.macaroons) == 1
    assert result.macaroons[0].session_id == "session-456"
    assert result.macaroons[0].revoked_at == "2024-06-01T10:00:00Z"
    mock_httpx_client.post.assert_called_once_with(
        "/v1/tokens/revoke", json={"session-id": "session-123"}
    )


def test_macaroon_info_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "account": {
                "id": "account-123",
                "email": "user@example.com",
                "username": "testuser",
                "display-name": "Test User",
                "validation": "verified",
            },
            "permissions": ["package-upload", "package-manage"],
            "packages": [
                {"id": "pkg-123", "name": "test-package", "type": "charm"},
                {"name": "another-package", "type": "snap"},
            ],
            "channels": ["stable", "edge"],
        },
    )

    result = publisher_gateway.macaroon_info()

    assert isinstance(result, MacaroonInfo)
    assert result.account.id == "account-123"
    assert result.account.email == "user@example.com"
    assert result.account.username == "testuser"
    assert result.account.display_name == "Test User"
    assert result.permissions == ["package-upload", "package-manage"]
    assert result.packages is not None
    assert len(result.packages) == 2
    assert result.packages[0].id == "pkg-123"
    assert result.packages[0].name == "test-package"
    assert result.packages[0].type == "charm"
    assert result.channels == ["stable", "edge"]
    mock_httpx_client.get.assert_called_once_with("/v1/tokens/whoami")


def test_push_resource_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"status-url": "/status/123"}
    )

    request = PushResourceRequest(upload_id="upload-123")

    result = publisher_gateway.push_resource("my-package", "my-resource", request)

    assert isinstance(result, PushResourceResponse)
    mock_httpx_client.post.assert_called_once_with(
        "/v1/charm/my-package/resources/my-resource/revisions",
        json={"upload_id": "upload-123"},
    )


def test_push_revision_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"status-url": "/status/456"}
    )

    request = PushRevisionRequest(upload_id="upload-456")

    result = publisher_gateway.push_revision("my-package", request)

    assert isinstance(result, PushRevisionResponse)
    mock_httpx_client.post.assert_called_once_with(
        "/v1/charm/my-package/revisions", json={"upload_id": "upload-456"}
    )


def test_list_resources_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "resources": [
                {
                    "name": "test-resource",
                    "type": "file",
                    "optional": False,
                    "revision": 42,
                },
                {"name": "optional-resource", "type": "oci-image", "optional": True},
            ]
        },
    )

    result = publisher_gateway.list_resources("my-package")

    assert len(result) == 2
    assert result[0].name == "test-resource"
    assert result[0].type == "file"
    assert result[0].optional is False
    assert result[0].revision == 42
    assert result[1].name == "optional-resource"
    assert result[1].type == "oci-image"
    assert result[1].optional is True
    assert result[1].revision is None
    mock_httpx_client.get.assert_called_once_with(
        "/v1/charm/my-package/resources", params={}
    )


def test_list_resources_with_revision(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "resources": [
                {
                    "name": "test-resource",
                    "type": "file",
                    "optional": False,
                    "revision": 42,
                }
            ]
        },
    )

    result = publisher_gateway.list_resources("my-package", revision=123)

    assert len(result) == 1
    assert result[0].name == "test-resource"
    mock_httpx_client.get.assert_called_once_with(
        "/v1/charm/my-package/resources", params={"revision": "123"}
    )


def test_list_resource_revisions_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(200, json={"revisions": []})

    result = publisher_gateway.list_resource_revisions("my-package", "my-resource")

    assert isinstance(result, ResourceRevisionsList)
    mock_httpx_client.get.assert_called_once_with(
        "/v1/charm/my-package/resources/my-resource/revisions"
    )


def test_update_resource_revisions_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.patch.return_value = httpx.Response(
        200, json={"num-resource-revisions-updated": 2}
    )

    updates = [
        ResourceRevisionUpdateRequest(
            revision=1, bases=[{"name": "ubuntu", "channel": "20.04"}]
        ),
        ResourceRevisionUpdateRequest(
            revision=2, bases=[{"name": "ubuntu", "channel": "22.04"}]
        ),
    ]

    result = publisher_gateway.update_resource_revisions(
        "my-package", "my-resource", updates
    )

    assert isinstance(result, UpdateResourceRevisionsResponse)
    assert result.num_resource_revisions_updated == 2
    mock_httpx_client.patch.assert_called_once()


def test_update_resource_revisions_empty_updates_raises_error(
    publisher_gateway: publisher.PublisherGateway,
):
    with pytest.raises(
        ValueError, match="Need at least one resource revision to update"
    ):
        publisher_gateway.update_resource_revisions("my-package", "my-resource", [])


def test_update_package_metadata_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.patch.return_value = httpx.Response(
        200,
        json={
            "metadata": {
                "id": "package-123",
                "name": "my-package",
                "title": "My Package",
                "summary": "New summary",
                "description": "New description",
                "contact": "contact@example.com",
                "website": "https://example.com",
                "default-track": "latest",
                "private": False,
                "status": "active",
                "store": "charmhub",
                "type": "charm",
                "authority": None,
                "links": {
                    "website": ["https://example.com"],
                    "docs": ["https://docs.example.com"],
                },
                "media": [{"type": "icon", "url": "https://example.com/icon.png"}],
                "publisher": {
                    "id": "pub-123",
                    "email": "publisher@example.com",
                    "username": "publisher",
                    "display-name": "Publisher Name",
                    "validation": "verified",
                },
                "track-guardrails": [],
                "tracks": [],
            }
        },
    )

    request = UpdatePackageMetadataRequest(
        summary="New summary", description="New description", default_track="latest"
    )

    result = publisher_gateway.update_package_metadata("my-package", request)

    assert isinstance(result, UpdatePackageMetadataResponse)
    assert result.metadata.id == "package-123"
    assert result.metadata.summary == "New summary"
    assert result.metadata.description == "New description"
    assert result.metadata.default_track == "latest"
    assert result.metadata.links is not None
    assert result.metadata.links["website"] == ["https://example.com"]
    assert result.metadata.media is not None
    assert len(result.metadata.media) == 1
    assert result.metadata.media[0].type == "icon"
    assert result.metadata.publisher.username == "publisher"

    mock_httpx_client.patch.assert_called_once_with(
        "/v1/charm/my-package",
        json={
            "summary": "New summary",
            "description": "New description",
            "default-track": "latest",
        },
    )


def test_list_upload_reviews_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "revisions": [
                {
                    "upload-id": "upload-123",
                    "status": "approved",
                    "revision": 42,
                    "errors": None,
                },
                {
                    "upload-id": "upload-456",
                    "status": "needs_review",
                    "revision": None,
                    "errors": [
                        {"code": "validation-error", "message": "Invalid manifest"}
                    ],
                },
            ]
        },
    )

    result = publisher_gateway.list_upload_reviews("my-package")

    assert len(result) == 2
    assert result[0].upload_id == "upload-123"
    assert result[0].status == "approved"
    assert result[0].revision == 42
    assert result[1].upload_id == "upload-456"
    assert result[1].revision is None
    assert result[1].errors is not None
    assert len(result[1].errors) == 1
    mock_httpx_client.get.assert_called_once_with(
        "/v1/charm/my-package/revisions/review", params={}
    )


def test_list_upload_reviews_with_upload_id(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "revisions": [
                {
                    "upload-id": "upload-123",
                    "status": "approved",
                    "revision": 42,
                    "errors": None,
                }
            ]
        },
    )

    result = publisher_gateway.list_upload_reviews("my-package", upload_id="upload-123")

    assert len(result) == 1
    assert result[0].upload_id == "upload-123"
    mock_httpx_client.get.assert_called_once_with(
        "/v1/charm/my-package/revisions/review", params={"upload-id": "upload-123"}
    )


def test_oci_image_resource_upload_credentials_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "image-name": "test-image",
            "username": "test-user",
            "password": "test-password",
        },
    )

    result = publisher_gateway.oci_image_resource_upload_credentials(
        "my-package", "my-resource"
    )

    assert isinstance(result, OciImageResourceUploadCredentialsResponse)
    assert result.image_name == "test-image"
    assert result.username == "test-user"
    assert result.password == "test-password"  # noqa: S105
    mock_httpx_client.get.assert_called_once_with(
        "/v1/charm/my-package/resources/my-resource/oci-image/upload-credentials"
    )


def test_oci_image_resource_blob_success(
    mock_httpx_client: mock.Mock, publisher_gateway: publisher.PublisherGateway
):
    mock_httpx_client.post.return_value = httpx.Response(
        200,
        json={
            "ImageName": "test-image:latest",
            "Username": "test-user",
            "Password": "test-password",
        },
    )

    result = publisher_gateway.oci_image_resource_blob(
        "my-package", "my-resource", "sha256:abc123"
    )

    assert isinstance(result, OciImageResourceBlobResponse)
    assert result.image_name == "test-image:latest"
    assert result.username == "test-user"
    assert result.password == "test-password"  # noqa: S105
    mock_httpx_client.post.assert_called_once_with(
        "/v1/charm/my-package/resources/my-resource/oci-image/blob",
        json={"image-digest": "sha256:abc123"},
    )


def test_upload_file_success(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    tmp_path,
):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"successful": True, "upload_id": "upload-123"}
    )

    result = publisher_gateway.upload_file(test_file)

    assert result == "upload-123"
    mock_httpx_client.post.assert_called_once_with(
        "/unscanned-upload/",
        files={"binary": ("test.txt", mock.ANY, "application/octet-stream")},
    )


def test_upload_file_unsuccessful(
    mock_httpx_client: mock.Mock,
    publisher_gateway: publisher.PublisherGateway,
    tmp_path,
):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    mock_httpx_client.post.return_value = httpx.Response(
        200, json={"successful": False, "error": "Upload failed"}
    )

    with pytest.raises(errors.CraftStoreError, match="Server error while pushing file"):
        publisher_gateway.upload_file(test_file)
