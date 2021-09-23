# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Canonical Ltd.
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
from typing import Any, Dict, Final, Sequence


@dataclasses.dataclass(repr=True)
class Endpoints:
    """Endpoints used to make requests to a store.

    :param whoami: path to the whoami API.
    :param tokens: path to the tokens API.
    :param tokens_exchange: path to the tokens_exchange API.
    """

    whoami: str
    tokens: str
    tokens_exchange: str

    @staticmethod
    def get_token_request(
        *, permissions: Sequence[str], description: str, ttl: int
    ) -> Dict[str, Any]:
        """Return a properly formatted request for a token request.

        Permissions can be selected from :data:`craft_store.attenuations`

        :param permissions: a list of permissions to use.
        :param description: description that identifies the client.
        :param ttl: time to live for the requested token.
        """
        return {
            "permissions": permissions,
            "description": description,
            "ttl": ttl,
        }


@dataclasses.dataclass(repr=True)
class _SnapStoreEndpoints(Endpoints):
    """Snap Store endpoints used to make requests to a store."""

    @staticmethod
    def get_token_request(
        *, permissions: Sequence[str], description: str, ttl: int
    ) -> Dict[str, Any]:
        return {
            "attenuations": permissions,
            "description": description,
            "expiry": ttl,
        }


CHARMHUB: Final = Endpoints(
    whoami="/v1/whoami",
    tokens="/v1/tokens",
    tokens_exchange="/v1/tokens/exchange",
)
"""Charmhub set of supported endpoints."""


SNAP_STORE: Final = _SnapStoreEndpoints(
    whoami="/api/v2/tokens/whoami",
    tokens="/api/v2/tokens",
    tokens_exchange="/api/v2/tokens/exchange",
)
"""Snap Store set of supported endpoints."""
