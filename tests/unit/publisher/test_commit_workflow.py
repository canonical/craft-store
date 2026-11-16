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
"""Tests for commit-workflows PublisherGateway API."""

from typing import Any
from unittest import mock

import httpx
import pytest
from craft_store import errors
from craft_store.models import Plane
from craft_store.publisher import (
    ORIGIN_REMOTE_NAME,
    CraftPublisherGateway,
)

from .conftest import dict_with_optional_plane


def _fake_commit_workflow_response(
    *,
    commit_workflow_id: str = "9121",
    commit_hash: str = "test-commit-hash",
    channel_name: str = "test-latest/edge",
    channel_track: str = "test-latest",
    channel_risk: str = "edge",
    status: str = "succeeded",
    channel_branch: str | None = None,
    buildsets: list[dict[str, str]] | None = None,
    error_list: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    error_list = error_list or []
    buildsets = buildsets or []
    return {
        "id": commit_workflow_id,
        "commit-hash": commit_hash,
        "craft-channel": {
            "name": channel_name,
            "track": channel_track,
            "risk": channel_risk,
            "branch": channel_branch,
        },
        "buildsets": buildsets,
        "status": status,
        "error-list": error_list,
        "created-at": "2024-10-02T20:33:38.650564+00:00",
        "completed-at": "2024-10-02T20:34:04.458915+00:00",
    }


@pytest.fixture
def commit_workflows_endpoint() -> str:
    return "/v1/craft/commit-workflows"


def test_trigger_commit_workflow(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane | None,
    commit_workflows_endpoint: str,
) -> None:
    """Test getting remotes for given package."""
    package_name = "test-package-1"
    fake_workflow_id = f"{package_name}-commit-workflow-1234"
    test_commit = "test-commit-sha"
    release_channel = "test-latest/edge"

    mock_httpx_client.post.return_value = httpx.Response(
        200,
        json={
            "commit-workflow-id": fake_workflow_id,
        },
    )

    commit_workflow_id = craft_publisher_gateway.start_commit_workflow(
        test_commit,
        channel=release_channel,
        package_name=package_name,
    )

    assert commit_workflow_id == fake_workflow_id, (
        "Fake commit workflow id should be returned."
    )
    mock_httpx_client.post.assert_called_with(
        commit_workflows_endpoint,
        json=dict_with_optional_plane(
            {
                "action": "commit",
                "channel": release_channel,
                "commit-hash": test_commit,
                "package-name": package_name,
                "package-type": craft_publisher_gateway._namespace,
                "origin-name": ORIGIN_REMOTE_NAME,
            },
            default_plane,
        ),
    )


def test_trigger_commit_workflow_incorrect_response(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane | None,
    commit_workflows_endpoint: str,
) -> None:
    """Test getting remotes for given package."""
    package_name = "test-package-1"
    test_commit = "test-commit-sha"
    release_channel = "test-latest/edge"

    mock_httpx_client.post.return_value = httpx.Response(
        200,
        json={"maformed_response": "some-val"},
    )

    with pytest.raises(errors.InvalidResponseError):
        _ = craft_publisher_gateway.start_commit_workflow(
            test_commit,
            channel=release_channel,
            package_name=package_name,
        )


@pytest.mark.parametrize("fake_workflow_id", [None, "fake-commit-workflow-341"])
def test_get_commit_workflows(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane,
    fake_workflow_id: str | None,
    commit_workflows_endpoint: str,
) -> None:
    """Test getting remotes for given package."""
    package_name = "test-package-1"

    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "commit-workflows": [
                _fake_commit_workflow_response(
                    commit_workflow_id=fake_workflow_id or "missing-workflow-id"
                ),
            ]
        },
    )

    commit_workflows = craft_publisher_gateway.get_commit_workflows(
        fake_workflow_id,
        package_name=package_name,
    )

    assert len(commit_workflows) == 1, (
        "There should be at least single workflow returned."
    )

    expected_params = dict_with_optional_plane(
        {
            "commit-workflow-id": fake_workflow_id,
            "package": f"{craft_publisher_gateway._namespace}/{package_name}",
        },
        default_plane,
    )
    if fake_workflow_id is None:
        expected_params.pop("commit-workflow-id")
    mock_httpx_client.get.assert_called_with(
        commit_workflows_endpoint,
        params=expected_params,
    )


@pytest.mark.parametrize("fake_workflow_id", [None, "fake-commit-workflow-341"])
def test_get_commit_workflows_error_response(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane | None,
    fake_workflow_id: str | None,
    commit_workflows_endpoint: str,
) -> None:
    """Test getting remotes for given package."""
    package_name = "test-package-1"

    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={
            "commit-workflows": [
                _fake_commit_workflow_response(
                    commit_workflow_id=fake_workflow_id or "missing-workflow-id",
                    error_list=[{"code": "error", "message": "something bad happened"}],
                ),
            ]
        },
    )

    with pytest.raises(
        errors.CraftStoreError,
        match="Error returned from store: something bad happened",
    ):
        _ = craft_publisher_gateway.get_commit_workflows(
            fake_workflow_id,
            package_name=package_name,
            raise_on_error=True,
        )

    expected_params = dict_with_optional_plane(
        {
            "commit-workflow-id": fake_workflow_id,
            "package": f"{craft_publisher_gateway._namespace}/{package_name}",
        },
        default_plane,
    )
    if fake_workflow_id is None:
        expected_params.pop("commit-workflow-id")
    mock_httpx_client.get.assert_called_with(
        commit_workflows_endpoint,
        params=expected_params,
    )


def test_get_commit_workflows_incorrect_response(
    craft_publisher_gateway: CraftPublisherGateway,
    mock_httpx_client: mock.Mock,
    default_plane: Plane | None,
) -> None:
    """Test getting remotes for given package."""
    package_name = "test-package-1"

    mock_httpx_client.get.return_value = httpx.Response(
        200,
        json={"maformed_response": "some-val"},
    )

    with pytest.raises(errors.InvalidResponseError):
        _ = craft_publisher_gateway.get_commit_workflows(
            package_name=package_name,
        )
