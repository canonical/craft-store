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
"""Client for the publisher gateway."""

from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Final, Literal, cast
from urllib.parse import urlparse

import httpx
import pydantic

from craft_store import errors
from craft_store._httpx_auth import CandidAuth, DeveloperTokenAuth, UbuntuOneAuth
from craft_store.auth import Auth
from craft_store.models import Plane
from craft_store.models import RegisteredNameModel as RegisteredName

from ._response import (
    Buildset,
    CommitWorkflow,
    ReleaseResult,
    Releases,
    Remote,
    Revision,
    SourceStoreOperationStatus,
    StoreEntityReference,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Generator, Sequence

    from . import _request
    from ._request import (
        BuildsetCreateRequest,
        BuildsetsStatusRequest,
        CommitWorkflowRequest,
        PromoteWorkflowRequest,
        UpdateRemoteRequest,
    )


ORIGIN_REMOTE_NAME: Final[str] = "origin"
UPSTREAM_REMOTE_NAME: Final[str] = "upstream"
STORE_REMOTE_NAME: Final[str] = "store"

TRACK_NAME_REGEX = re.compile(r"^[a-zA-Z0-9](?:[_.-]?[a-zA-Z0-9])*$")
"""A regular expression guarding track names.

Retrieved from https://api.staging.charmhub.io/docs/default/#create-tracks
"""

logger = logging.getLogger(__name__)


@contextmanager
def _pydantic_validation_context(data: dict[str, Any]) -> Generator[None]:
    """Raise CraftStoreError if validation of the data fails."""
    try:
        yield
    except pydantic.ValidationError as err:
        logger.debug("incorrect data received from the store: %s", data)
        raise errors.CraftStoreError("incorrect data received from the store") from err


class PublisherGateway:
    """Client for the publisher gateway.

    This class is a client wrapper for the Canonical Publisher Gateway.
    The latest version of the server API can be seen at: https://api.charmhub.io/docs/

    Each instance is only valid for one particular namespace.
    """

    def __init__(
        self,
        base_url: str,
        namespace: str,
        auth: httpx.Auth | Auth,
        *,
        plane: Plane | None = None,
        timeout: float = 60.0,
    ) -> None:
        """Create a publisher gateway client.

        :param base_url: The base URL of the publisher gateway API.
        :param namespace: The package namespace (e.g. ``"charm"`` or ``"snap"``).
        :param auth: Either an :class:`httpx.Auth` instance (used directly), or a
            craft-store :class:`~craft_store.auth.Auth` instance (wrapped in
            :class:`~craft_store._httpx_auth.CandidAuth` automatically).
        :param plane: Optional default plane for source package operations.
        :param timeout: Timeout for HTTP requests in seconds. Defaults to 60.0.
        """
        self._namespace = namespace
        self._plane = plane
        if isinstance(auth, httpx.Auth):
            httpx_auth = auth
        else:
            httpx_auth = CandidAuth(auth=auth, auth_type="macaroon")
        self._client = httpx.Client(
            base_url=base_url,
            auth=httpx_auth,
            timeout=timeout,
        )

    @classmethod
    def with_developer_token(
        cls,
        base_url: str,
        namespace: str,
        auth: Auth,
        *,
        plane: Plane | None = None,
        timeout: float = 30.0,
    ) -> PublisherGateway:
        """Create a publisher gateway client using Developer Token authentication.

        :param base_url: The base URL of the publisher gateway API.
        :param namespace: The package namespace (e.g. ``"rock"`` or ``"bundle"``).
        :param auth: A :class:`~craft_store.auth.Auth` instance for keyring access.
        :param plane: Optional default plane for source package operations.
        :param timeout: Timeout for HTTP requests in seconds. Defaults to 30.0.
        """
        httpx_auth = DeveloperTokenAuth(auth=auth, auth_type="macaroon")
        return cls(
            base_url=base_url,
            namespace=namespace,
            auth=httpx_auth,
            plane=plane,
            timeout=timeout,
        )

    @classmethod
    def with_ubuntu_one(
        cls,
        base_url: str,
        namespace: str,
        *,
        auth: Auth | None = None,
        application_name: str = "craft-store",
        client_description: str = "craft-store",
    ) -> PublisherGateway:
        """Create a publisher gateway client using Ubuntu One SSO authentication.

        This is a convenience constructor that creates the :class:`UbuntuOneAuth`
        internally. Credentials must already be saved in the system keyring (e.g.
        by calling :meth:`~craft_store.login.UbuntuOneLogin.login_with` first).

        :param base_url: The base URL of the publisher gateway API (e.g.
            ``"https://api.charmhub.io"``).
        :param namespace: The package namespace (e.g. ``"charm"`` or ``"snap"``).
        :param auth: An optional :class:`~craft_store.auth.Auth` instance for
            keyring access. If not provided, one is created automatically using
            ``application_name`` and the host derived from ``base_url``.
        :param application_name: The application name used for keyring storage.
            Must match the name used when credentials were saved. Defaults to
            ``"craft-store"``.
        :param client_description: A description passed to the store during token
            exchange. Defaults to ``"craft-store"``.
        """
        if auth is None:
            auth = Auth(
                application_name=application_name,
                host=urlparse(base_url).netloc,
            )
        httpx_auth = UbuntuOneAuth(
            auth=auth,
            api_base_url=base_url,
            client_description=client_description,
        )
        return cls(base_url=base_url, namespace=namespace, auth=httpx_auth)

    @staticmethod
    def _check_error(response: httpx.Response) -> None:
        """Check a response for general errors.

        :param response: an httpx response from the server.
        :raises: InvalidResponseError if the response from the server is invalid.
        :raises: CraftStoreError if the response status code is an error code.
        """
        if response.is_success:
            return
        try:
            error_response = response.json()
        except (JSONDecodeError, UnicodeDecodeError) as exc:
            logger.debug(f"Error response: {response.text}")
            raise errors.InvalidResponseError(response) from exc

        error_list = error_response.get("error-list", [])
        if response.status_code >= 500:
            brief = f"Store had an error ({response.status_code})"
        else:
            brief = f"Error {response.status_code} returned from store"
        if len(error_list) == 1:
            brief = f"{brief}: {error_list[0].get('message')}"
        else:
            fancy_error_list = errors.StoreErrorList(error_list)
            brief = f"{brief}.\n{fancy_error_list}"

        if error_list:
            # Log the errors, but don't pass them to CraftStoreError or they will be
            # duplicated.
            logger.debug(f"Errors from the store:\n{errors.StoreErrorList(error_list)}")

        try:
            request = response.request
        except RuntimeError:
            details = None
        else:
            details = f"Error occurred on {request.method} request to {request.url}"
            if request.content and logger.isEnabledFor(logging.DEBUG):
                content = request.content
                max_len = 2048
                decoded = content[:max_len].decode("utf-8", errors="replace")
                suffix = (
                    ""
                    if len(content) <= max_len
                    else f"... (truncated, {len(content)} bytes total)"
                )
                logger.debug("Request content: %s%s", decoded, suffix)

        raise errors.CraftStoreError(brief, details=details)

    @staticmethod
    def _check_keys(
        response: httpx.Response, expected_keys: set[str]
    ) -> dict[str, Any]:
        """Check that a json dictionary has the expected keys.

        :param json_response: The deserialised JSON from the server.
        :param expected_keys: A set of keys that are expected in the JSON.
        :returns: The deserialised JSON from the server.
        :raises: InvalidResponseError if the response from the server is invalid.
        """
        try:
            json_response = response.json()
        except (JSONDecodeError, UnicodeDecodeError) as exc:
            logger.debug(f"Server response: {response.text}")
            raise errors.InvalidResponseError(response) from exc
        if not isinstance(json_response, dict):
            logger.debug(f"Server response: {response.text}")
            raise errors.InvalidResponseError(response)
        received_expected_keys = expected_keys & json_response.keys()
        missing_keys = expected_keys - received_expected_keys
        if missing_keys:
            logger.debug(f"Server response: {response.text}")
            raise errors.InvalidResponseError(
                response, details=f"Missing JSON keys: {missing_keys}"
            )
        return json_response

    def list_registered_names(
        self, include_collaborations: bool = False
    ) -> Sequence[RegisteredName]:
        """Return names registered by the authenticated user.

        :param include_collaborations: if True, includes names the user is a
            collaborator on but does not own.
        :returns: A sequence of names registered to the user.

        API docs: https://api.charmhub.io/docs/default/#list-registered-names
        """
        response = self._client.get(
            f"/v1/{self._namespace}",
            params={"include-collaborations": include_collaborations},
        )
        self._check_error(response)
        results = self._check_keys(response, expected_keys={"results"})["results"]
        return [RegisteredName.unmarshal(item) for item in results]

    def whoami(self) -> dict[str, Any]:
        """Return whoami json data.

        API docs: https://api.charmhub.io/docs/default/#macaroon-info
        """
        response = self._client.get("/v1/tokens/whoami")
        self._check_error(response)
        return self._check_keys(response, expected_keys=set())

    def register_name(
        self,
        name: str,
        *,
        entity_type: str,
        private: bool = False,
        team: str | None = None,
    ) -> str:
        """Register a name on the store.

        :param name: the name to register.
        :param entity_type: The type of package to register (e.g. charm or snap)
        :param private: Whether this entity is private or not.
        :param team: An optional team ID to register the name with.

        :returns: the ID of the registered name.
        """
        request_json = {
            "name": name,
            "private": private,
            "type": entity_type,
        }
        if team is not None:
            request_json["team"] = team

        response = self._client.post(f"/v1/{self._namespace}", json=request_json)
        self._check_error(response)
        return str(self._check_keys(response, expected_keys={"id"})["id"])

    def get_package_metadata(self, name: str) -> RegisteredName:
        """Get general metadata for a package.

        :param name: The name of the package to query.
        :returns: A dictionary matching the result from the publisher gateway.

        API docs: https://api.charmhub.io/docs/default/#package-metadata
        """
        response = self._client.get(
            url=f"/v1/{self._namespace}/{name}",
        )
        self._check_error(response)
        return RegisteredName.unmarshal(
            self._check_keys(response, expected_keys={"metadata"})["metadata"]
        )

    def unregister_name(self, name: str) -> str:
        """Unregister a name with no published packages.

        :param name: The name to unregister.

        :returns: the ID of the deleted name.

        API docs: https://api.charmhub.io/docs/default/#unregister-package
        """
        response = self._client.delete(f"/v1/{self._namespace}/{name}")
        self._check_error(response)
        return str(
            self._check_keys(response, expected_keys={"package-id"})["package-id"]
        )

    def list_revisions(
        self,
        name: str,
        *,
        fields: Collection[str] | None = None,
        include_craft_yaml: bool = False,
        revision: int | None = None,
    ) -> Sequence[Revision]:
        """List the revisions for a specific name.

        :param name: The name of the package to query.
        :param fields: A list of fields to include. These vary by namespace and are only
            checked server-side.
        :param include_craft_yaml: Whether to include the craft YAML file in the response.
        :param revision: If provided, get only the specified revision.
        :returns: A list of revisions in the store and their metadata.

        API docs: https://api.charmhub.io/docs/default/#list-revisions
        """
        params = {}
        if fields is not None:
            params["fields"] = ",".join(fields)
        if include_craft_yaml:
            params["include-craft-yaml"] = "true"
        if revision is not None:
            params["revision"] = str(revision)
        response = self._client.get(
            f"/v1/{self._namespace}/{name}/revisions", params=params
        )
        self._check_error(response)
        response_data = self._check_keys(response, {"revisions"})
        return [Revision.unmarshal(revision) for revision in response_data["revisions"]]

    def list_releases(self, name: str) -> Releases:
        """Get the information about the releases of a name.

        :param name: The name of the package to query.
        :returns: Channel info, package info and revision info.

        The revision information returned is only for the revisions that are currently
        published in a channel.

        API docs: https://api.charmhub.io/docs/default/#list-releases
        """
        response = self._client.get(f"/v1/{self._namespace}/{name}/releases")
        self._check_error(response)
        return Releases.unmarshal(response.json())

    def release(
        self, name: str, requests: list[_request.ReleaseRequest]
    ) -> Sequence[ReleaseResult]:
        response = self._client.post(
            f"/v1/{self._namespace}/{name}/releases", json=requests
        )
        self._check_error(response)

        return [
            ReleaseResult.unmarshal(rel)
            for rel in self._check_keys(response, {"released"})["released"]
        ]

    def create_tracks(self, name: str, *tracks: _request.CreateTrackRequest) -> int:
        """Create one or more tracks in the store.

        :param name: The store name (i.e. the specific charm, snap or other package)
            to which this track will be attached.
        :param tracks: Each track is a dictionary mapping query values.
        :returns: The number of tracks created by the store.
        :raises: InvalidRequestError if the name field of any passed track is invalid.

        API docs: https://api.charmhub.io/docs/default/#create-tracks
        """
        bad_track_names = {
            track["name"]
            for track in tracks
            if not TRACK_NAME_REGEX.match(track["name"]) or len(track["name"]) > 28
        }
        if bad_track_names:
            bad_tracks = ", ".join(sorted(bad_track_names))
            raise errors.InvalidRequestError(
                f"The following track names are invalid: {bad_tracks}",
                resolution="Ensure all tracks have valid names.",
            )

        response = self._client.post(
            f"/v1/{self._namespace}/{name}/tracks", json=tracks
        )
        self._check_error(response)

        return int(
            self._check_keys(response, expected_keys={"num-tracks-created"})[
                "num-tracks-created"
            ]
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
