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
"""Test for list_revisions API."""

from typing import Any, cast
from unittest import mock

import httpx
import pytest
from craft_store import errors
from craft_store.publisher import PublisherGateway


@pytest.fixture(
    params=[None, "342372933f7caf6c37ad9bf4b587aca1c6f06d97"],
    ids=["without_commit", "with_commit"],
)
def commit(request: pytest.FixtureRequest) -> str | None:
    return cast(str | None, request.param)


@pytest.fixture(
    params=[
        pytest.param(
            {
                "revisions": [
                    {
                        "craft": {"commit": "<to-be-updated>"},
                        "created-at": "2025-02-03T14:30:56Z",
                        "revision": 1,
                        "size": 39168,
                        "status": "released",
                        "version": "90a8c2f",
                    }
                ]
            },
            id="bin",
        ),
        pytest.param(
            {
                "revisions": [
                    {
                        "craft": {"commit": "<to-be-updated>"},
                        "created-at": "2025-02-03T20:23:09Z",
                        "revision": 1,
                        "status": "released",
                    }
                ]
            },
            id="rock",
        ),
    ]
)
def fake_revision(request: pytest.FixtureRequest, commit: str | None) -> dict[str, Any]:
    revisions_result: dict[str, Any] = request.param
    revisions_result["revisions"][0]["craft"]["commit"] = commit
    return revisions_result


@pytest.fixture
def multiple_revisions() -> dict[str, Any]:
    return {
        "revisions": [
            {
                "craft": {"commit": "c622c06f7ecdebf16eadf84d7dfaea291ab768a9"},
                "created-at": "2024-10-25T12:34:07Z",
                "revision": 1,
                "size": 38912,
                "status": "approved",
                "version": "git",
            },
            {
                "craft": {"commit": None},
                "created-at": "2024-11-20T15:38:27Z",
                "revision": 12,
                "size": 38612,
                "status": "approved",
                "version": "git",
            },
            {
                "craft": {"commit": None},
                "created-at": "2025-01-10T22:30:31Z",
                "revision": 20,
                "size": 39576,
                "status": "released",
                "version": "a98737b",
            },
            {
                "created-at": "2025-01-23T16:34:29Z",
                "revision": 25,
                "size": 39436,
                "status": "approved",
                "version": "1.4g",
            },
            {
                "craft": {"commit": None},
                "created-at": "2025-01-31T17:31:37Z",
                "revision": 26,
                "size": 39244,
                "status": "released",
                "version": "1.4g",
            },
        ]
    }


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param(["test-f1"], id="single_field"),
        pytest.param(["test-f1", "f2", "f3"], id="multiple_fields"),
        pytest.param(
            ["revision", "size", "status", "version", "created-at"],
            id="real_fields",
        ),
    ],
)
def test_list_revision(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    fake_revision: dict[str, Any],
    commit: str | None,
    fields: list[str],
) -> None:
    test_package_name = "test-package"
    mock_httpx_client.get.return_value = httpx.Response(
        httpx.codes.OK,
        json=fake_revision,
    )

    revisions = craft_publisher_gateway.list_revisions(
        test_package_name,
        fields=fields,
    )

    assert len(revisions) == 1

    assert revisions[0].status == "released"
    craft_release = revisions[0].craft
    assert craft_release is not None
    if commit is None:
        assert craft_release.commit is None
    else:
        assert craft_release.commit == commit

    mock_httpx_client.get.assert_called_with(
        f"/v1/{craft_publisher_gateway._namespace}/{test_package_name}/revisions",
        params={"fields": ",".join(fields)},
    )


def test_list_multiple_revisions(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    multiple_revisions: dict[str, Any],
) -> None:
    test_package_name = "test-package"
    mock_httpx_client.get.return_value = httpx.Response(
        httpx.codes.OK,
        json=multiple_revisions,
    )

    revisions = craft_publisher_gateway.list_revisions(test_package_name)

    assert len(revisions) == 5

    mock_httpx_client.get.assert_called_with(
        f"/v1/{craft_publisher_gateway._namespace}/{test_package_name}/revisions",
        params={},
    )


def test_list_revision_error_response(
    mock_httpx_client: mock.Mock,
    craft_publisher_gateway: PublisherGateway,
    invalid_store_response: httpx.Response,
) -> None:
    test_package_name = "test-package"
    mock_httpx_client.get.return_value = invalid_store_response
    with pytest.raises(errors.CraftStoreError):
        craft_publisher_gateway.list_revisions(
            test_package_name,
        )
