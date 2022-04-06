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

"""Endpoint definitions for different services."""

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Final, Optional, Sequence, Type

from craft_store.models import (
    MarshableModel,
    charm_list_releases_model,
    snap_list_releases_model,
)


@dataclasses.dataclass(frozen=True)
class Package:
    """Representation of a package name and type."""

    package_name: str
    package_type: str


@dataclasses.dataclass(repr=True)
class Endpoints:  # pylint: disable=too-many-instance-attributes
    """Endpoints used to make requests to a store.

    :param namespace: the namespace to use for endpoints.
    :param whoami: path to the whoami API.
    :param upload: path used for uploading.
    :param tokens: path to the tokens API.
    :param tokens_exchange: path to the tokens_exchange API.
    :param tokens_refresh: path to the tokens_refresh API.
    :param list_releases_model: list_releases response model.
    """

    namespace: str
    whoami: str
    upload: str
    tokens: str
    tokens_exchange: str
    list_releases_model: Type[MarshableModel]
    valid_package_types: Sequence[str]
    tokens_refresh: Optional[str] = None

    def _validate_packages(self, packages: Sequence[Package]) -> None:
        unknown_packages = [
            p for p in packages if p.package_type not in self.valid_package_types
        ]
        if unknown_packages:
            unknown_package_types = [p.package_type for p in unknown_packages]
            raise ValueError(
                f"Package types {unknown_package_types} not in {self.valid_package_types}"
            )

    def get_token_request(
        self,
        *,
        permissions: Sequence[str],
        description: str,
        ttl: int,
        channels: Optional[Sequence[str]] = None,
        packages: Optional[Sequence[Package]] = None,
    ) -> Dict[str, Any]:
        """Return a properly formatted request for a token request.

        Permissions can be selected from :data:`craft_store.attenuations`

        :param permissions: a list of permissions to use.
        :param description: description that identifies the client.
        :param ttl: time to live for the requested token.
        :param packages: a sequence of :attr:`Package` to limit the requested token to.
        :param channels: a sequence of channels to limit the requested token to.
        """
        token_request = {
            "permissions": permissions,
            "description": description,
            "ttl": ttl,
        }

        if packages:
            self._validate_packages(packages)
            token_request["packages"] = [
                {"type": p.package_type, "name": p.package_name} for p in packages
            ]

        if channels:
            token_request["channels"] = channels

        return token_request

    @staticmethod
    def get_upload_id(result: Dict[str, Any]) -> str:
        """Return the upload ID for a given result.

        :param result: the result from an upload request.
        """
        return result["upload_id"]


@dataclasses.dataclass(repr=True)
class _SnapStoreEndpoints(Endpoints):
    """Snap Store endpoints used to make requests to a store."""

    def get_token_request(
        self,
        *,
        permissions: Sequence[str],
        description: str,
        ttl: int,
        channels: Optional[Sequence[str]] = None,
        packages: Optional[Sequence[Package]] = None,
    ) -> Dict[str, Any]:
        expires = (
            datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc)
            + timedelta(seconds=ttl)
        ).isoformat()

        token_request: Dict[str, Any] = {
            "permissions": permissions,
            "description": description,
            "expires": expires,
        }

        if packages:
            self._validate_packages(packages)
            token_request["packages"] = [
                # Originally, snaps were supposed to be versioned by series,
                # this all changed with the introduction of bases.
                {"series": "16", "name": p.package_name}
                for p in packages
            ]

        if channels:
            token_request["channels"] = channels

        return token_request

    @staticmethod
    def get_upload_id(result: Dict[str, Any]) -> str:
        return result["upload_id"]


CHARMHUB: Final = Endpoints(
    namespace="charm",
    whoami="/v1/tokens/whoami",
    upload="/unscanned-upload/",
    tokens="/v1/tokens",
    tokens_exchange="/v1/tokens/exchange",
    valid_package_types=["charm", "bundle"],
    list_releases_model=charm_list_releases_model.ListReleasesModel,
)
"""Charmhub set of supported endpoints."""


SNAP_STORE: Final = _SnapStoreEndpoints(
    namespace="snap",
    whoami="/api/v2/tokens/whoami",
    upload="/unscanned-upload/",
    tokens="/api/v2/tokens",
    tokens_exchange="/api/v2/tokens/exchange",
    valid_package_types=["snap"],
    list_releases_model=snap_list_releases_model.ListReleasesModel,
)
"""Snap Store set of supported endpoints."""


U1_SNAP_STORE: Final = _SnapStoreEndpoints(
    namespace="snap",
    whoami="/api/v2/tokens/whoami",
    upload="/unscanned-upload/",
    tokens="/dev/api/acl/",
    tokens_exchange="/api/v2/tokens/discharge",
    tokens_refresh="/api/v2/tokens/refresh",
    valid_package_types=["snap"],
    list_releases_model=snap_list_releases_model.ListReleasesModel,
)
"""Ubuntu One compatible Snap Store set of supported endpoints."""
