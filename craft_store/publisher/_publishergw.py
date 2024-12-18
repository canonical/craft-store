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

import re
from json import JSONDecodeError
from typing import TYPE_CHECKING

import httpx

from craft_store import errors, models
from craft_store._httpx_auth import CandidAuth
from craft_store.auth import Auth

if TYPE_CHECKING:
    from . import _request


TRACK_NAME_REGEX = re.compile(r"^[a-zA-Z0-9](?:[_.-]?[a-zA-Z0-9])*$")
"""A regular expression guarding track names.

Retrieved from https://api.staging.charmhub.io/docs/default.html#create_tracks
"""


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
    def _check_error(response: httpx.Response, expected_keys: set[str]) -> None:
        """Check a response for general errors.

        :param response: an httpx response from the server.
        :param expected_keys: A set of expected keys in the JSON response.
        :raises: InvalidResponseError if the response from the server is invalid.
        :raises: CraftStoreError if the response status code is an error code.
        """
        if not expected_keys and response.is_success:
            return
        try:
            error_response = response.json()
        except JSONDecodeError as exc:
            raise errors.InvalidResponseError(response) from exc

        if response.is_success:
            if not isinstance(error_response, dict):
                raise errors.InvalidResponseError(response)
            received_expected_keys = expected_keys & error_response.keys()
            missing_keys = expected_keys - received_expected_keys
            if missing_keys:
                raise errors.InvalidResponseError(
                    response, details=f"Missing JSON keys: {missing_keys}"
                )
            return
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
        raise errors.CraftStoreError(
            brief, store_errors=errors.StoreErrorList(error_list)
        )

    def list_registered_names(
        self, include_collaborations: bool = False
    ) -> list[models.RegisteredNameModel]:
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
        self._check_error(response, expected_keys={"results"})
        return [
            models.RegisteredNameModel.unmarshal(item)
            for item in response.json()["results"]
        ]

    def register_name(
        self,
        name: str,
        *,
        entity_type: str | None = None,
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
        }
        if team is not None:
            request_json["team"] = team
        if entity_type is not None:
            request_json["type"] = entity_type

        response = self._client.post(f"/v1/{self._namespace}", json=request_json)
        self._check_error(response, expected_keys={"id"})
        return str(response.json()["id"])

    def get_package_metadata(self, name: str) -> models.RegisteredNameModel:
        """Get general metadata for a package.

        :param name: The name of the package to query.
        :returns: A dictionary matching the result from the publisher gateway.

        API docs: https://api.charmhub.io/docs/default.html#package_metadata
        """
        response = self._client.get(
            url=f"/v1/{self._namespace}/{name}",
        )
        self._check_error(response, expected_keys={"metadata"})
        return models.RegisteredNameModel.unmarshal(response.json()["metadata"])

    def unregister_name(self, name: str) -> str:
        """Unregister a name with no published packages.

        :param name: The name to unregister.

        :returns: the ID of the deleted name.

        API docs: https://api.charmhub.io/docs/default.html#unregister_package
        """
        response = self._client.delete(f"/v1/{self._namespace}/{name}")
        self._check_error(response, expected_keys={"package-id"})
        return str(response.json()["package-id"])

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
        self._check_error(response, expected_keys={"num-tracks-created"})

        return int(response.json()["num-tracks-created"])
