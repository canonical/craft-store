# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021-2022 Canonical Ltd.
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

"""Craft Store BaseClient."""

import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import urlparse

import requests
from requests_toolbelt import (  # type: ignore[import]
    MultipartEncoder,
    MultipartEncoderMonitor,
)

from . import endpoints, errors, models
from .auth import Auth
from .http_client import HTTPClient
from .models.resource_revision_model import (
    CharmResourceRevision,
    CharmResourceRevisionUpdateRequest,
    CharmResourceType,
    RequestCharmResourceBaseList,
)
from .models.revisions_model import RevisionModel

logger = logging.getLogger(__name__)


class BaseClient(metaclass=ABCMeta):
    """Encapsulates API calls for the Snap Store or Charmhub.

    :param base_url: the base url of the API endpoint.
    :param storage_base_url: the base url for storage.
    :param endpoints: :data:`.endpoints.CHARMHUB` or :data:`.endpoints.SNAP_STORE`.
    :param application_name: the name application using this class, used for the keyring.
    :param user_agent: User-Agent header to use for HTTP(s) requests.
    :param environment_auth: environment variable to use for credentials.
    :param ephemeral: keep everything in memory.

    :raises errors.NoKeyringError: if there is no usable keyring.
    """

    def __init__(
        self,
        *,
        base_url: str,
        storage_base_url: str,
        endpoints: endpoints.Endpoints,
        application_name: str,
        user_agent: str,
        environment_auth: str | None = None,
        ephemeral: bool = False,
        file_fallback: bool = False,
    ) -> None:
        """Initialize the Store Client."""
        self.http_client = HTTPClient(user_agent=user_agent)

        self._base_url = base_url
        self._storage_base_url = storage_base_url
        self._endpoints = endpoints

        self._auth = Auth(
            application_name,
            urlparse(base_url).netloc,
            environment_auth=environment_auth,
            ephemeral=ephemeral,
            file_fallback=file_fallback,
        )

    @abstractmethod
    def _get_discharged_macaroon(  # type: ignore[no-untyped-def]
        self, root_macaroon: str, **kwargs
    ) -> str:
        """Return a discharged macaroon ready to use in an Authorization header."""

    @abstractmethod
    def _get_authorization_header(self) -> str:
        """Return the authorization header content to use."""

    def _get_macaroon(self, token_request: dict[str, Any]) -> str:
        token_response = self.http_client.request(
            "POST",
            self._base_url + self._endpoints.tokens,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=token_request,
        )

        return str(token_response.json()["macaroon"])

    def login(  # type: ignore[no-untyped-def]
        self,
        *,
        permissions: Sequence[str],
        description: str,
        ttl: int,
        packages: Sequence[endpoints.Package] | None = None,
        channels: Sequence[str] | None = None,
        **kwargs,
    ) -> str:
        """Obtain credentials to perform authenticated requests.

        Credentials are stored on the system's keyring, handled by
        :data:`craft_store.auth.Auth`.

        The list of permissions to select from can be referred to on
        :data:`craft_store.attenuations`.

        The login process requires 3 steps:

        - request an initial macaroon on :attr:`.endpoints.Endpoints.tokens`.
        - discharge that macaroon using Candid
        - send the discharge macaroon to :attr:`.endpoints.Endpoints.tokens_exchange`
          to obtain final authorization of the macaroon

        This last macaroon is stored into the system's keyring to
        perform authenticated requests.

        :param permissions: Set of permissions to grant the login.
        :param description: Client description to refer to from the Store.
        :param ttl: time to live for the credential, in other words, how
                    long until it expires, expressed in seconds.
        :param packages: Sequence of packages to limit the credentials to.
        :param channels: Sequence of channel names to limit the credentials to.

        :raises errors.CredentialsAlreadyAvailable: if credentials already exist.
        """
        # Early check to ensure credentials do not already exist.
        self._auth.ensure_no_credentials()

        token_request = self._endpoints.get_token_request(
            permissions=permissions,
            description=description,
            ttl=ttl,
            packages=packages,
            channels=channels,
        )

        macaroon = self._get_macaroon(token_request)
        store_authorized_macaroon = self._get_discharged_macaroon(macaroon, **kwargs)

        # Save the authorization token.
        self._auth.set_credentials(store_authorized_macaroon)

        return self._auth.encode_credentials(store_authorized_macaroon)

    def request(  # type: ignore[no-untyped-def]
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> requests.Response:
        """Perform an authenticated request if auth_headers are True.

        :param method: HTTP method used for the request.
        :param url: URL to request with method.
        :param params: Query parameters to be sent along with the request.
        :param headers: Headers to be sent along with the request.

        :raises errors.StoreServerError: for error responses.
        :raises errors.NetworkError: for lower level network issues.
        :raises errors.CredentialsUnavailable: if credentials cannot be found.

        :return: Response from the request.
        """
        if headers is None:
            headers = {}

        headers["Authorization"] = self._get_authorization_header()

        return self.http_client.request(
            method,
            url,
            params=params,
            headers=headers,
            **kwargs,
        )

    def whoami(self) -> dict[str, Any]:
        """Return whoami json data queyring :attr:`.endpoints.Endpoints.whoami`."""
        return dict(self.request("GET", self._base_url + self._endpoints.whoami).json())

    def logout(self) -> None:
        """Clear credentials.

        :raises errors.CredentialsUnavailable: if credentials cannot be found.
        """
        self._auth.del_credentials()

    def upload_file(
        self,
        *,
        filepath: Path,
        monitor_callback: Callable | None = None,  # type: ignore[type-arg]
    ) -> str:
        """Upload filepath to storage.

        The monitor_callback is a method receiving one argument of type
        ``MultipartEncoder``, the total length of the upload can be accessed
        from this encoder from the ``len`` attribute to setup a progress bar
        instance.

        The callback is to return a function that receives a
        ``MultipartEncoderMonitor`` from which the ``.bytes_read`` attribute
        can be read to update progress.

        The simplest implementation can look like:

        .. code-block:: python

          def monitor_callback(encoder: requests_toolbelt.MultipartEncoder):

              # instantiate progress class with total bytes encoder.len

              def progress_printer(monitor: requests_toolbelt.MultipartEncoderMonitor):
                 # Print progress using monitor.bytes_read

              return progress_printer

        :param monitor_callback: a callback to monitor progress.

        """
        file_size = filepath.stat().st_size
        logger.debug(
            "Beginning to upload a file %r with size of %r bytes",
            str(filepath),
            file_size,
        )

        with filepath.open("rb") as upload_file:
            encoder = MultipartEncoder(
                fields={
                    "binary": (filepath.name, upload_file, "application/octet-stream")
                }
            )

            # create a monitor (so that progress can be displayed) as call the real pusher
            if monitor_callback is not None:
                monitor = MultipartEncoderMonitor(encoder, monitor_callback(encoder))
            else:
                monitor = MultipartEncoderMonitor(encoder)

            response = self.http_client.request(
                "POST",
                self._storage_base_url + self._endpoints.upload,
                headers={
                    "Content-Type": monitor.content_type,
                    "Accept": "application/json",
                },
                data=monitor,
            )

        result = response.json()
        if not result["successful"]:
            raise errors.CraftStoreError(f"Server error while pushing file: {result}")

        upload_id = self._endpoints.get_upload_id(result)
        logger.debug("Uploading bytes for %r ended, id %r", str(filepath), upload_id)

        return upload_id

    def notify_revision(
        self,
        *,
        name: str,
        revision_request: models.revisions_model.RevisionsRequestModel,
    ) -> models.revisions_model.RevisionsResponseModel:
        """Post to the revisions endpoint to notify the store about an upload.

        This request usually takes place after a successful :attr:`.upload`.
        """
        endpoint = self._endpoints.get_revisions_endpoint(name)
        response = self.request(
            "POST", self._base_url + endpoint, json=revision_request.marshal()
        ).json()

        return models.revisions_model.RevisionsResponseModel.unmarshal(response)

    def push_resource(
        self,
        name: str,
        resource_name: str,
        *,
        upload_id: str,
        resource_type: CharmResourceType | None = None,
        bases: RequestCharmResourceBaseList | None = None,
    ) -> str:
        """Push a resource revision to the server.

        :param name: the (snap, charm, etc.) name to attach the upload to
        :param resource_name: The name of the resource.
        :param upload_id: The ID of the upload (the output of :attr:`.upload`)
        :param resource_type: If necessary for the namespace, the type of resource.
        :param bases: A list of bases that this file supports.

        :returns: The path and query string (as a single string) of the status URL.

        API docs: http://api.staging.charmhub.io/docs/default.html#push_resource

        The status URL returned is likely a pointer to ``list_upload_reviews``:
        http://api.staging.charmhub.io/docs/default.html#list_upload_reviews
        """
        endpoint = self._base_url + self._endpoints.get_resource_revisions_endpoint(
            name, resource_name
        )
        request_model: dict[str, str | list[dict[str, Any]]] = {
            "upload-id": upload_id,
        }
        if resource_type:
            request_model["type"] = resource_type
        if bases:
            request_model["bases"] = [
                base.model_dump(exclude_defaults=False) for base in bases
            ]

        response = self.request("POST", endpoint, json=request_model)
        response_model = response.json()
        return str(response_model["status-url"])

    def list_revisions(self, name: str) -> list[RevisionModel]:
        """Get the list of existing revisions for a package.

        :param name: the package to lookup.
        :returns: a list of revisions that have been uploaded for this package.

        Charmhub example: https://api.charmhub.io/docs/default.html#list_revisions
        """
        endpoint = self._endpoints.get_revisions_endpoint(name)
        response = self.request("GET", self._base_url + endpoint).json()

        return [RevisionModel.unmarshal(r) for r in response["revisions"]]

    def list_resource_revisions(
        self, name: str, resource_name: str
    ) -> list[CharmResourceRevision]:
        """List the revisions for a specific resource of a specific name."""
        namespace = self._endpoints.namespace
        if namespace != "charm":
            raise NotImplementedError(
                f"Cannot get resource revisions in namespace {namespace}."
            )
        endpoint = f"/v1/{namespace}/{name}/resources/{resource_name}/revisions"
        response = self.request("GET", self._base_url + endpoint)
        model = response.json()

        return [CharmResourceRevision.unmarshal(r) for r in model["revisions"]]

    def update_resource_revisions(
        self,
        *updates: CharmResourceRevisionUpdateRequest,
        name: str,
        resource_name: str,
    ) -> int:
        """Update one or more resource revisions.

        :param name: The package.
        :param resource_name: The resource name to update.
        :param updates: The updates to make of any revisions
        :returns: The number of revisions updated.

        """
        if not updates:
            raise ValueError("Need at least one resource revision to update.")
        if (namespace := self._endpoints.namespace) != "charm":
            raise NotImplementedError(
                f"Cannot update resource revisions in namespace {namespace}."
            )
        endpoint = f"/v1/{namespace}/{name}/resources/{resource_name}/revisions"

        body = {
            "resource-revision-updates": [update.model_dump() for update in updates]
        }

        response = self.request("PATCH", self._base_url + endpoint, json=body).json()

        return cast(int, response["num-resource-revisions-updated"])

    def update_resource_revision(
        self,
        name: str,
        resource_name: str,
        *,
        revision: int,
        bases: RequestCharmResourceBaseList,
    ) -> int:
        """Update a single resource revision."""
        return self.update_resource_revisions(
            CharmResourceRevisionUpdateRequest(revision=revision, bases=bases),
            name=name,
            resource_name=resource_name,
        )

    def get_list_releases(self, *, name: str) -> models.MarshableModel:
        """Query the list_releases endpoint and return the result."""
        endpoint = f"/v1/{self._endpoints.namespace}/{name}/releases"
        response = self.request("GET", self._base_url + endpoint).json()

        return self._endpoints.list_releases_model.unmarshal(response)

    def release(
        self,
        *,
        name: str,
        release_request: Sequence[models.release_request_model.ReleaseRequestModel],
    ) -> None:
        """Request a release of name.

        :param name: name to release.
        :param release_request: sequence of items to release.
        """
        endpoint = f"/v1/{self._endpoints.namespace}/{name}/releases"

        self.request(
            "POST",
            self._base_url + endpoint,
            json=[r.marshal() for r in release_request],
        )

    def list_registered_names(
        self, *, include_collaborations: bool = False
    ) -> list[models.RegisteredNameModel]:
        """List the registered names available to the logged in account.

        :param include_collaborations: if True, includes names the user is a
            collaborator on but does not own.
        """
        endpoint = f"/v1/{self._endpoints.namespace}"
        params = {
            "include-collaborations": "true" if include_collaborations else "false",
        }
        response = self.request("GET", self._base_url + endpoint, params=params)
        results = response.json().get("results", [])
        return [models.RegisteredNameModel.unmarshal(item) for item in results]

    def register_name(
        self,
        name: str,
        *,
        entity_type: Literal["charm", "bundle", "snap"] | None = None,
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
        endpoint = f"/v1/{self._endpoints.namespace}"

        request_json = {
            "name": name,
            "private": private,
        }
        if team is not None:
            request_json["team"] = team
        if entity_type is not None:
            request_json["type"] = entity_type

        response = self.request("POST", self._base_url + endpoint, json=request_json)
        return str(response.json()["id"])

    def unregister_name(self, name: str) -> str:
        """Unregister a name with no published packages.

        :param name: The name to unregister.

        :returns: the ID of the deleted name.
        """
        endpoint = f"/v1/{self._endpoints.namespace}/{name}"
        response = self.request("DELETE", self._base_url + endpoint)

        return str(response.json()["package-id"])
