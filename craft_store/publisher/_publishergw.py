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
from collections.abc import Callable, Collection, Sequence
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import annotated_types
import httpx

from craft_store import errors
from craft_store._httpx_auth import CandidAuth
from craft_store.auth import Auth
from craft_store.models import RegisteredNameModel as RegisteredName
from craft_store.models.resource_revision_model import CharmResourceRevision

from ._response import (
    AuthenticatedMacaroonResponse,
    ExchangeDashboardMacaroonsResponse,
    ExchangeMacaroonResponse,
    GetMacaroonResponse,
    MacaroonInfo,
    MacaroonResponse,
    OciImageResourceBlobResponse,
    OciImageResourceUploadCredentialsResponse,
    OfflineExchangeMacaroonResponse,
    PushResourceResponse,
    PushRevisionResponse,
    ReleaseResult,
    Releases,
    ResourceInfo,
    Revision,
    UnauthenticatedMacaroonResponse,
    UpdatePackageMetadataResponse,
    UpdateResourceRevisionsResponse,
    UploadReview,
)

if TYPE_CHECKING:
    from . import _request

from ._request import (
    BaseDict,
    MacaroonRequest,
    PackageDict,
    PackageLinks,
    Permission,
    PushResourceRequest,
    PushRevisionRequest,
    ResourceRevisionUpdateRequest,
    ResourceType,
    UpdatePackageMetadataRequest,
)

TRACK_NAME_REGEX = re.compile(r"^[a-zA-Z0-9](?:[_.-]?[a-zA-Z0-9])*$")
"""A regular expression guarding track names.

Retrieved from https://api.staging.charmhub.io/docs/default.html#create_tracks
"""

logger = logging.getLogger(__name__)


class PublisherGateway:
    """Client for the publisher gateway.

    This class is a client wrapper for the Canonical Publisher Gateway.
    The latest version of the server API can be seen at: https://api.charmhub.io/docs/

    Each instance is only valid for one particular namespace.
    """

    def __init__(self, base_url: str, namespace: str, auth: Auth) -> None:
        self._namespace = namespace
        self._client = httpx.Client(
            base_url=base_url,
            auth=CandidAuth(auth=auth, auth_type="macaroon"),
        )

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
        except JSONDecodeError as exc:
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

        raise errors.CraftStoreError(brief)

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
        except JSONDecodeError as exc:
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

        API docs: https://api.charmhub.io/docs/default.html#list_registered_names
        """
        response = self._client.get(
            f"/v1/{self._namespace}",
            params={"include-collaborations": include_collaborations},
        )
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys={"results"})
        return [RegisteredName.unmarshal(item) for item in response_data["results"]]

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
        response_data = self._check_keys(response, expected_keys={"id"})
        return str(response_data["id"])

    def get_package_metadata(self, name: str) -> RegisteredName:
        """Get general metadata for a package.

        :param name: The name of the package to query.
        :returns: A dictionary matching the result from the publisher gateway.

        API docs: https://api.charmhub.io/docs/default.html#package_metadata
        """
        response = self._client.get(
            url=f"/v1/{self._namespace}/{name}",
        )
        self._check_error(response)
        return RegisteredName.unmarshal(response.json()["metadata"])

    def unregister_name(self, name: str) -> str:
        """Unregister a name with no published packages.

        :param name: The name to unregister.

        :returns: the ID of the deleted name.

        API docs: https://api.charmhub.io/docs/default.html#unregister_package
        """
        response = self._client.delete(f"/v1/{self._namespace}/{name}")
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys={"package-id"})
        return str(response_data["package-id"])

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

        API docs: https://api.charmhub.io/docs/default.html#list_revisions
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

        API docs: https://api.charmhub.io/docs/default.html#list_releases
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

        API docs: https://api.charmhub.io/docs/default.html#create_tracks
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

        return int(response.json()["num-tracks-created"])

    def get_macaroon(self, include_inactive: bool = False) -> GetMacaroonResponse:
        """Get existing macaroons for authenticated account, or bakery v2 macaroon for unauthenticated.

        :param include_inactive: Whether to include inactive macaroons.
        :returns: Either existing macaroons or a bakery v2 macaroon for discharge.

        API docs: https://api.charmhub.io/docs/default.html#get_macaroon
        """
        params = {}
        if include_inactive:
            params["include-inactive"] = "true"

        response = self._client.get("/v1/tokens", params=params)
        self._check_error(response)

        response_data = response.json()
        # Try to unmarshal as AuthenticatedMacaroonResponse first
        if "macaroons" in response_data:
            return AuthenticatedMacaroonResponse.unmarshal(response_data)
        # Otherwise, unmarshal as UnauthenticatedMacaroonResponse
        return UnauthenticatedMacaroonResponse.unmarshal(response_data)

    def issue_macaroon(
        self,
        *,
        permissions: Annotated[Collection[Permission], annotated_types.MinLen(1)]
        | None = None,
        description: str | None = None,
        ttl: Annotated[int, annotated_types.Ge(10)] | None = None,
        packages: Annotated[Collection[PackageDict], annotated_types.MinLen(1)]
        | None = None,
        channels: Annotated[Collection[str], annotated_types.MinLen(1)] | None = None,
    ) -> MacaroonResponse:
        """Issue a new macaroon with specified permissions and constraints.

        :param permissions: List of permissions to grant.
        :param description: Description of the macaroon usage.
        :param ttl: Time to live in seconds (minimum 10).
        :param packages: Package restrictions.
        :param channels: Channel restrictions.
        :returns: The macaroon response with the issued macaroon.

        API docs: https://api.charmhub.io/docs/default.html#issue_macaroon
        """
        request = MacaroonRequest(
            permissions=set(permissions) if permissions is not None else None,
            description=description,
            ttl=ttl,
            packages=set(packages) if packages is not None else None,
            channels=set(channels) if channels is not None else None,
        )
        response = self._client.post(
            "/v1/tokens",
            json=request.model_dump(exclude_none=True),
        )
        self._check_error(response)
        return MacaroonResponse.unmarshal(response.json())

    def exchange_macaroons(self, macaroon: str) -> ExchangeMacaroonResponse:
        """Exchange discharged macaroons for store credentials.

        :param macaroon: The discharged macaroon to exchange.
        :returns: The exchanged macaroon response.

        API docs: https://api.charmhub.io/docs/default.html#exchange_macaroons
        """
        response = self._client.post(
            "/v1/tokens/exchange",
            json={"macaroon": macaroon},
        )
        self._check_error(response)
        return ExchangeMacaroonResponse.unmarshal(response.json())

    def offline_exchange_macaroon(
        self, macaroon: str
    ) -> OfflineExchangeMacaroonResponse:
        """Exchange macaroons offline for store admin authentication.

        :param macaroon: The macaroon to exchange offline.
        :returns: The exchanged offline macaroon response.

        API docs: https://api.charmhub.io/docs/default.html#offline_exchange_macaroon
        """
        response = self._client.post(
            "/v1/tokens/offline/exchange",
            json={"macaroon": macaroon},
        )
        self._check_error(response)
        return OfflineExchangeMacaroonResponse.unmarshal(response.json())

    def revoke_macaroon(self, session_id: str) -> str:
        """Revoke a macaroon.

        :param session_id: The session ID of the macaroon to revoke.
        :returns: The session ID of the revoked macaroon.

        API docs: https://api.charmhub.io/docs/default.html#revoke_macaroon
        """
        response = self._client.post(
            "/v1/tokens/revoke",
            json={"session-id": session_id},
        )
        self._check_error(response)
        return session_id

    def macaroon_info(self) -> MacaroonInfo:
        """Get information about the authenticated macaroon token.

        :returns: Information about the authenticated macaroon and account.

        API docs: https://api.charmhub.io/docs/default.html#macaroon_info
        """
        response = self._client.get("/v1/tokens/whoami")
        self._check_error(response)
        return MacaroonInfo.unmarshal(
            self._check_keys(
                response,
                expected_keys={"account", "permissions", "packages", "channels"},
            )
        )

    def exchange_dashboard_macaroons(
        self,
        discharged_macaroons: str,
        *,
        description: str | None = None,
    ) -> ExchangeDashboardMacaroonsResponse:
        """Exchange dashboard.snapcraft.io SSO discharged macaroons for a developer token.

        The macaroons are passed in as the Authorization header.

        :param discharged_macaroons: Dashboard SSO discharged macaroons for authorization.
        :param description: Optional client description.
        :returns: The developer token response.

        API docs: https://api.charmhub.io/docs/default.html#exchange_dashboard_macaroons
        """
        json_data = {}
        if description is not None:
            json_data["client-description"] = description

        response = self._client.post(
            "/v1/tokens/dashboard/exchange",
            json=json_data,
            headers={"Authorization": discharged_macaroons},
        )
        self._check_error(response)
        return ExchangeDashboardMacaroonsResponse.unmarshal(response.json())

    def push_resource(
        self,
        name: str,
        resource_name: str,
        *,
        upload_id: str,
        resource_type: ResourceType | None = None,
        bases: Sequence[BaseDict] | None = None,
    ) -> PushResourceResponse:
        """Push a resource revision to the server.

        :param name: The package name to attach the upload to.
        :param resource_name: The name of the resource.
        :param upload_id: ID of the upload.
        :param resource_type: Resource type.
        :param bases: Supported bases.
        :returns: The push resource response with status URL.

        API docs: https://api.charmhub.io/docs/default.html#push_resource
        """
        request = PushResourceRequest(
            upload_id=upload_id, type=resource_type, bases=bases
        )
        response = self._client.post(
            f"/v1/{self._namespace}/{name}/resources/{resource_name}/revisions",
            json=request.model_dump(exclude_none=True),
        )
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys={"status-url"})
        return PushResourceResponse.unmarshal(
            {"status_url": response_data["status-url"]}
        )

    def push_revision(
        self,
        name: str,
        *,
        upload_id: str,
    ) -> PushRevisionResponse:
        """Push/notify a revision to the server.

        :param name: The package name to attach the upload to.
        :param upload_id: ID of the upload.
        :returns: The push revision response with status URL.

        API docs: https://api.charmhub.io/docs/default.html#push_revision
        """
        request = PushRevisionRequest(upload_id=upload_id)
        response = self._client.post(
            f"/v1/{self._namespace}/{name}/revisions",
            json=request.model_dump(exclude_none=True),
        )
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys={"status-url"})
        return PushRevisionResponse.unmarshal(
            {"status_url": response_data["status-url"]}
        )

    def list_resources(
        self, name: str, *, revision: int | None = None
    ) -> Sequence[ResourceInfo]:
        """List existing declared resources for a package.

        :param name: The name of the package to query.
        :param revision: Optional specific revision to list resources for.
        :returns: A sequence of declared resources for the package.

        API docs: https://api.charmhub.io/docs/default.html#list_resources
        """
        params = {}
        if revision is not None:
            params["revision"] = str(revision)

        response = self._client.get(
            f"/v1/{self._namespace}/{name}/resources", params=params
        )
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys={"resources"})
        return [
            ResourceInfo.unmarshal(resource) for resource in response_data["resources"]
        ]

    def list_resource_revisions(
        self, name: str, resource_name: str
    ) -> list[CharmResourceRevision]:
        """List the revisions for a specific resource of a specific package.

        :param name: The name of the package to query.
        :param resource_name: The name of the resource to query.
        :returns: A list of resource revisions.

        API docs: https://api.charmhub.io/docs/default.html#list_resource_revisions
        """
        response = self._client.get(
            f"/v1/{self._namespace}/{name}/resources/{resource_name}/revisions"
        )
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys={"revisions"})
        return [
            CharmResourceRevision.unmarshal(revision)
            for revision in response_data["revisions"]
        ]

    def update_resource_revisions(
        self,
        name: str,
        resource_name: str,
        updates: Sequence[tuple[int, Sequence[BaseDict]]],
    ) -> UpdateResourceRevisionsResponse:
        """Update one or more resource revisions.

        :param name: The package name.
        :param resource_name: The resource name to update.
        :param updates: List of (revision, bases) tuples to update.
        :returns: The number of revisions updated.

        API docs: https://api.charmhub.io/docs/default.html#update_resource_revisions
        """
        if not updates:
            raise ValueError("Need at least one resource revision to update.")

        request_updates = [
            ResourceRevisionUpdateRequest(revision=revision, bases=bases)
            for revision, bases in updates
        ]

        request_body = {
            "resource-revision-updates": [
                update.model_dump(exclude_none=True) for update in request_updates
            ]
        }

        response = self._client.patch(
            f"/v1/{self._namespace}/{name}/resources/{resource_name}/revisions",
            json=request_body,
        )
        self._check_error(response)
        response_data = self._check_keys(
            response, expected_keys={"num-resource-revisions-updated"}
        )
        return UpdateResourceRevisionsResponse.unmarshal(response_data)

    def update_package_metadata(
        self,
        name: str,
        *,
        contact: str | None = None,
        default_track: str | None = None,
        description: str | None = None,
        links: PackageLinks | None = None,
        private: bool | None = None,
        summary: str | None = None,
        title: str | None = None,
        website: str | None = None,
    ) -> UpdatePackageMetadataResponse:
        """Update package metadata.

        :param name: The package name to update.
        :param contact: Contact information (legacy).
        :param default_track: Default track name.
        :param description: Package description.
        :param links: Package links.
        :param private: Whether package is private.
        :param summary: Package summary.
        :param title: Package title.
        :param website: Project website (legacy).
        :returns: The update response.

        API docs: https://api.charmhub.io/docs/default.html#update_package_metadata
        """
        request = UpdatePackageMetadataRequest(
            contact=contact,
            default_track=default_track,
            description=description,
            links=links,
            private=private,
            summary=summary,
            title=title,
            website=website,
        )
        response = self._client.patch(
            f"/v1/{self._namespace}/{name}",
            json=request.model_dump(exclude_none=True, by_alias=True),
        )
        self._check_error(response)
        return UpdatePackageMetadataResponse.unmarshal(response.json())

    def list_upload_reviews(
        self, name: str, *, upload_id: str | None = None
    ) -> Sequence[UploadReview]:
        """List existing uploads review status for a package.

        :param name: The package name to query.
        :param upload_id: Optional upload ID to view status of a specific upload.
        :returns: A sequence of upload review revisions.

        API docs: https://api.charmhub.io/docs/default.html#list_upload_reviews
        """
        params = {}
        if upload_id:
            params["upload-id"] = upload_id

        response = self._client.get(
            f"/v1/{self._namespace}/{name}/revisions/review", params=params
        )
        self._check_error(response)
        response_data = self._check_keys(response, expected_keys={"revisions"})
        return [UploadReview.unmarshal(review) for review in response_data["revisions"]]

    def oci_image_resource_upload_credentials(
        self,
        name: str,
        resource_name: str,
    ) -> OciImageResourceUploadCredentialsResponse:
        """Get Charmstore docker registry auth server credential for oci-image upload.

        Returns image name and Charmstore docker registry auth server credentials
        for a specific image upload to this registry.

        :param name: The package name.
        :param resource_name: The resource name.
        :returns: The upload credentials response.

        API docs: https://api.charmhub.io/docs/default.html#oci_image_resource_upload_credentials
        """
        response = self._client.get(
            f"/v1/{self._namespace}/{name}/resources/{resource_name}/oci-image/upload-credentials"
        )
        self._check_error(response)
        return OciImageResourceUploadCredentialsResponse.unmarshal(
            self._check_keys(
                response, expected_keys={"image-name", "username", "password"}
            )
        )

    def oci_image_resource_blob(
        self,
        name: str,
        resource_name: str,
        image_digest: str,
    ) -> OciImageResourceBlobResponse:
        """Return OCI-image resource blob as expected by Juju.

        :param name: The package name.
        :param resource_name: The resource name.
        :param image_digest: The image digest.
        :returns: The blob response with image credentials.

        API docs: https://api.charmhub.io/docs/default.html#oci_image_resource_blob
        """
        response = self._client.post(
            f"/v1/{self._namespace}/{name}/resources/{resource_name}/oci-image/blob",
            json={"image-digest": image_digest},
        )
        self._check_error(response)
        return OciImageResourceBlobResponse.unmarshal(
            self._check_keys(
                response, expected_keys={"ImageName", "Username", "Password"}
            )
        )

    def upload_file(
        self,
        filepath: Path,
        monitor_callback: Callable | None = None,  # type: ignore[type-arg] # noqa: ARG002
    ) -> str:
        """Upload filepath to storage.

        The monitor_callback is a method receiving one argument of type
        ``MultipartEncoder``, the total length of the upload can be accessed
        from this encoder from the ``len`` attribute to setup a progress bar
        instance.

        :param filepath: Path to the file to upload.
        :param monitor_callback: A callback to monitor progress.
        :returns: The upload ID.

        API docs: https://api.charmhub.io/docs/default.html#upload
        """
        try:
            with filepath.open("rb") as upload_file:
                files = {
                    "binary": (filepath.name, upload_file, "application/octet-stream")
                }
                response = self._client.post("/unscanned-upload/", files=files)

            self._check_error(response)
            result = response.json()

            if not result.get("successful", False):
                self._raise_upload_error(result)

            return str(result["upload_id"])
        except Exception as e:
            logger.debug(f"Upload failed for {filepath}: {e}")
            raise

    def _raise_upload_error(self, result: dict[str, Any]) -> None:
        """Raise an error for upload failures."""
        raise errors.CraftStoreError(f"Server error while pushing file: {result}")
