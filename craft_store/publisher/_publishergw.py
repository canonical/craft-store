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
    def _check_error(response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            error_response = response.json()
        except JSONDecodeError as exc:
            raise errors.CraftStoreError(
                f"Invalid response from server ({response.status_code})",
                details=response.text,
            ) from exc
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

    def get_package_metadata(self, name: str) -> models.RegisteredNameModel:
        """Get general metadata for a package.

        :param name: The name of the package to query.
        :returns: A dictionary matching the result from the publisher gateway.

        API docs: https://api.charmhub.io/docs/default.html#package_metadata
        """
        response = self._client.get(
            url=f"/v1/{self._namespace}/{name}",
        )
        self._check_error(response)
        return models.RegisteredNameModel.unmarshal(response.json()["metadata"])

    def create_tracks(self, name: str, *tracks: _request.CreateTrackRequest) -> int:
        """Create one or more tracks in the store.

        :param name: The store name (i.e. the specific charm, snap or other package)
            to which this track will be attached.
        :param tracks: Each track is a dictionary mapping query values.
        :returns: The number of tracks created by the store.
        :returns: InvalidRequestError if the name field of any passed track is invalid.

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
