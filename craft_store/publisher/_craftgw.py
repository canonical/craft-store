# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2025 Canonical Ltd.
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

"""Client for Source Store Publisher Gateway."""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Final, Literal, cast

import httpx
import pydantic

from craft_store import errors
from craft_store._httpx_auth import DeveloperTokenAuth
from craft_store.auth import Auth
from craft_store.models import Plane
from craft_store.publisher._publishergw import PublisherGateway
from craft_store.publisher._request import (
    BuildsetCreateRequest,
    BuildsetsStatusRequest,
    CommitWorkflowRequest,
    PromoteWorkflowRequest,
    UpdateRemoteRequest,
)
from craft_store.publisher._response import (
    Buildset,
    CommitWorkflow,
    Remote,
    SourceStoreOperationStatus,
    StoreEntityReference,
)

ORIGIN_REMOTE_NAME: Final[str] = "origin"
UPSTREAM_REMOTE_NAME: Final[str] = "upstream"
STORE_REMOTE_NAME: Final[str] = "store"

logger = logging.getLogger(__name__)


@contextmanager
def _pydantic_validation_context(data: dict[str, Any]) -> Generator[None]:
    """Raise CraftStoreError if validation of the data fails."""
    try:
        yield
    except pydantic.ValidationError as err:
        logger.debug("incorrect data received from the store: %s", data)
        raise errors.CraftStoreError("incorrect data received from the store") from err


class CraftPublisherGateway(PublisherGateway):
    """Client for the craft publisher gateway."""

    def __init__(
        self,
        base_url: str,
        namespace: str,
        auth: Auth,
        *,
        plane: Plane | None = None,
        timeout: float = 30.0,
    ) -> None:
        super().__init__(base_url, namespace, auth)
        self._plane = plane
        self._client = httpx.Client(
            base_url=base_url,
            auth=DeveloperTokenAuth(auth=auth, auth_type="macaroon"),
            timeout=timeout,
        )

    def get_remotes(
        self,
        package_name: str,
        *,
        package_type: str | None = None,
        plane: Plane | None = None,
        channel: str | None = None,
    ) -> list[Remote]:
        """Get all remotes associated with the given package.

        :param package_name: name of the package that we want to update remotes
        :param package_type: type of package to query, defaults to _namespace attribute
        :param plane: plane to query, defaults to _plane attribute
        :param channel: source channel associated with the remotes (for `store` remote
            only)

        :return: a list of Remote objects associated with the given package
        """
        package_type = package_type or self._namespace

        params: dict[str, Any] = {
            "package": f"{package_type}/{package_name}",
        }
        self._add_plane_to_dict(params, plane=plane)

        if channel:
            params["channel"] = channel

        response = self._client.get("/v1/craft/remotes", params=params)
        self._check_error(response)
        expected_key = "remotes"
        response_data = self._check_keys(response, expected_keys={expected_key})
        with _pydantic_validation_context(response_data):
            return [Remote.unmarshal(remote) for remote in response_data[expected_key]]

    def update_remote(
        self,
        *,
        action: Literal["setup", "remove"],
        package_name: str,
        remote_name: str,
        remote_type: Literal["managed", "external"],
        url: str | None = None,
        access_token: str | None = None,
        package_type: str | None = None,
        plane: Plane | None = None,
    ) -> Remote:
        """Update remote configuration in Store.

        :param action: select whether to setup or remove remote
        :param package_name: name of the package that we want to update remotes
        :param remote_name: name of the remote to update
        :param remote_type: type of the remote to update. Choices: "managed", "external"
        :param url: address of the given remote, required for "external" remote
        :param access_token: optional read-access credentials for the remote
        :param package_type: type of package to query, defaults to _namespace attribute
        :param plane: plane to query, defaults to _plane attribute

        :return: Remote object which represents entity that was created or removed
        :raises MissingUrlForExternalRemoteError: If URL is not provided for external
            remote
        :raises UrlProvidedForManagedRemoteError: If URL is provided for managed remote
        """
        package_type = package_type or self._namespace

        data: UpdateRemoteRequest = {
            "action": action,
            "type": remote_type,
            "name": remote_name,
            "package-type": package_type,
            "package-name": package_name,
        }
        self._add_plane_to_dict(data, plane=plane)

        if action == "setup":
            if remote_type == "external" and url is None:
                raise errors.MissingUrlForExternalRemoteError(
                    "Cannot set external remote without URL"
                )

            if remote_type == "managed" and url:
                raise errors.UrlProvidedForManagedRemoteError(
                    "Managed remote has to be setup without URL"
                )

        if access_token:
            data["access-token"] = access_token

        if url:
            data["url"] = url

        response = self._client.post("/v1/craft/remotes", json=data)
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys=set())
        with _pydantic_validation_context(response_data):
            return Remote.unmarshal(response_data)

    def start_commit_workflow(
        self,
        commit_hash: str,
        *,
        package_name: str,
        channel: str,
        action: Literal["commit"] = "commit",
        origin_name: str = ORIGIN_REMOTE_NAME,
        package_type: str | None = None,
        plane: Plane | None = None,
    ) -> str:
        """Start workflow based on the commit from the origin.

        :param commit_hash: commit, that store is requested to process
        :param package_name: name of the package associated with release request
        :param channel: target source-channel to release commit to
        :param origin_name: name of the remote, that store uses to pull commit from
        :param action: action to be performed on the given commit
        :param package_type: type of package to query, defaults to _namespace attribute
        :param plane: plane to query, defaults to _plane attribute

        :return: Unique commit-workflow identifier
        """
        package_type = package_type or self._namespace

        data: CommitWorkflowRequest = {
            "action": action,
            "package-type": package_type,
            "package-name": package_name,
            "commit-hash": commit_hash,
            "channel": channel,
            "origin-name": origin_name,
        }
        self._add_plane_to_dict(data, plane=plane)
        return self._post_commit_workflow(data)

    def start_promotion_workflow(
        self,
        *,
        package_name: str,
        source_channel: str,
        plane: Plane | None = None,
        package_type: str | None = None,
    ) -> str:
        """Start a commit workflow to promote a commit on a channel.

        :param package_name: name of the package associated with the promotion request
        :param source_channel: the channel that contains the commit to promote
        :param package_type: type of package to query, defaults to _namespace attribute
        :param plane: plane to query, defaults to _plane attribute

        :return: Unique commit-workflow identifier
        """
        package_type_str = package_type or self._namespace

        data: PromoteWorkflowRequest = {
            "action": "promote",
            "package-type": package_type_str,
            "package-name": package_name,
            "source-channel": source_channel,
        }
        self._add_plane_to_dict(data, plane=plane)
        return self._post_commit_workflow(data)

    def _post_commit_workflow(
        self, data: CommitWorkflowRequest | PromoteWorkflowRequest
    ) -> str:
        response = self._client.post("/v1/craft/commit-workflows", json=data)
        self._check_error(response)
        expected_key = "commit-workflow-id"
        response_data = self._check_keys(response, expected_keys={expected_key})
        return cast(str, response_data[expected_key])

    def get_commit_workflows(
        self,
        commit_workflow_id: str | None = None,
        *,
        package_name: str,
        package_type: str | None = None,
        plane: Plane | None = None,
        raise_on_error: bool = False,
    ) -> list[CommitWorkflow]:
        """Get status of commit workflows associated with given package.

        :param commit_workflow_id: Optional id of the commit workflow
        :param package_name: name of the package associated with release request
        :param package_type: type of package to query, defaults to _namespace attribute
        :param plane: plane to query, defaults to _plane attribute
        :param raise_on_error: whether to raise if the first workflow contains errors

        :return: list of CommitWorkflow objects representing workflow statuses
        """
        package_type = package_type or self._namespace

        params = {
            "package": f"{package_type}/{package_name}",
        }
        self._add_plane_to_dict(params, plane=plane)
        if commit_workflow_id:
            params["commit-workflow-id"] = commit_workflow_id

        response = self._client.get("/v1/craft/commit-workflows", params=params)
        self._check_error(response)
        expected_key = "commit-workflows"
        response_data = self._check_keys(response, expected_keys={expected_key})
        commit_workflows = response_data[expected_key]
        if commit_workflows and raise_on_error:
            self._raise_if_error(
                error_list=commit_workflows[0].get("error-list", []),
                status_code=response.status_code,
            )
        with _pydantic_validation_context(response_data):
            return [
                CommitWorkflow.unmarshal(data) for data in response_data[expected_key]
            ]

    def _raise_if_error(
        self,
        *,
        error_list: list[dict[str, str]],
        status_code: int,
    ) -> None:
        if not error_list:
            return
        logger.debug("errors: %s", error_list)
        if httpx.codes.is_server_error(status_code):
            brief = f"Store had an error ({status_code})"
        elif httpx.codes.is_client_error(status_code):
            brief = f"Error ({status_code}) returned from store"
        else:
            brief = "Error returned from store"
        if len(error_list) == 1:
            brief = f"{brief}: {error_list[0].get('message')}"
        else:
            fancy_error_list = errors.StoreErrorList(error_list)
            brief = f"{brief}.\n{fancy_error_list}"
        raise errors.CraftStoreError(
            brief, store_errors=errors.StoreErrorList(error_list)
        )

    def create_buildset(
        self,
        *,
        package_name: str,
        channel: str,
        action: Literal["build"] = "build",
        package_type: str | None = None,
        plane: Plane | None = None,
    ) -> list[StoreEntityReference]:
        """Create new buildset for the given source channel.

        :param package_name: name of the package associated with release request
        :param channel: target channel which requires re-building
        :param action: action to perform on the buildset
        :param package_type: type of package to query, defaults to _namespace attribute
        :param plane: plane to query, defaults to _plane attribute

        :return: list of references to buildsets created by the request.
        """
        package_type = package_type or self._namespace

        data: BuildsetCreateRequest = {
            "action": action,
            "package-type": package_type,
            "package-name": package_name,
            "channel": channel,
        }
        self._add_plane_to_dict(data, plane=plane)

        response = self._client.post("/v1/craft/buildsets", json=data)
        self._check_error(response)
        expected_key = "buildsets"
        response_data = self._check_keys(response, expected_keys={expected_key})
        with _pydantic_validation_context(response_data):
            return [
                StoreEntityReference.unmarshal(data)
                for data in response_data[expected_key]
            ]

    def get_buildsets(
        self,
        *,
        package_name: str,
        buildset_id: str | None = None,
        channel: str | None = None,
        commit_hash: str | None = None,
        status: SourceStoreOperationStatus | None = None,
        package_type: str | None = None,
        plane: Plane | None = None,
    ) -> list[Buildset]:
        """Get buildsets associated with the given package.

        Additional filters may be supplied to limit number of results.

        :param package_name: name of the package related to buildsets
        :param buildset_id: prefix of the buildset to search for
        :param channel: filter to only show buildsets targeting specific channel
        :param commit_hash: filter to only show buildsets based on certain commit
        :param status: filter to only show builds with the specific status
        :param package_type: type of package to query, defaults to _namespace attribute
        :param plane: plane to query, defaults to _plane attribute

        :return: list of Buildset objects
        """
        package_type = package_type or self._namespace
        package = f"{package_type}/{package_name}"

        params: BuildsetsStatusRequest = {
            "package": package,
        }
        self._add_plane_to_dict(params, plane=plane)

        if commit_hash is not None:
            params["commit-hash"] = commit_hash

        if channel is not None:
            params["channel"] = channel

        if buildset_id is not None:
            params["buildset-id"] = buildset_id

        if status is not None:
            params["status"] = status.value

        response = self._client.get(
            "/v1/craft/buildsets", params=cast(dict[str, str], params)
        )

        self._check_error(response)
        expected_key = "buildsets"
        response_data = self._check_keys(response, expected_keys={expected_key})
        with _pydantic_validation_context(response_data):
            return [Buildset.unmarshal(data) for data in response_data[expected_key]]

    def get(self, url: str) -> httpx.Response:
        """Perform a GET request to the given URL, with authentication."""
        # Follow redirects by default, as many store urls require auth and then redirect
        # to a temporary address.
        response = self._client.get(url, follow_redirects=True)
        self._check_error(response)
        return response

    def _add_plane_to_dict(
        self,
        data_dict: BuildsetCreateRequest
        | BuildsetsStatusRequest
        | CommitWorkflowRequest
        | PromoteWorkflowRequest
        | UpdateRemoteRequest
        | dict[str, Any],
        *,
        plane: Plane | None,
    ) -> None:
        """Extract plane to the mapping if available."""
        plane = plane or self._plane
        if plane is not None:
            data_dict["plane-name"] = plane.plane_name
            data_dict["domain-name"] = plane.domain_name
