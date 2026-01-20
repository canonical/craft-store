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

"""Ubuntu One Login Client."""

import datetime
import os
from collections.abc import Collection
from urllib.parse import urlparse

import httpx
import pymacaroons

from craft_store.creds import DeveloperToken


class UbuntuOneLogin:
    """A client for handling logging into Ubuntu One.

    :param login_url: The base URL for logging in. If not given, selects from the
        ``CRAFT_LOGIN_URL`` environment variable or defaults to login.ubuntu.com.
    :param request_macaroon_url: The URL to query for getting a macaroon. This is expected to
        be the full URL, domain included, for an endpoint that matches the `Snapcraft
        Dashboard macaroon request API
        <https://dashboard.snapcraft.io/docs/reference/v1/macaroon.html#request-a-macaroon>`_. If not given, selects from the ``CRAFT_REQUEST_MACAROON_URL``
        environment variable or defaults to the snapcraft dashboard URL.
    """

    def __init__(
        self,
        *,
        login_url: str | None = None,
        request_macaroon_url: str | None = None,
    ) -> None:
        """Create a login class."""
        if login_url:
            self._login_url = login_url
        else:
            self._login_url = os.environ.get(
                "CRAFT_LOGIN_URL", "https://login.ubuntu.com"
            )

        if request_macaroon_url:
            self._request_macaroon_url = request_macaroon_url
        else:
            self._request_macaroon_url = os.environ.get(
                "CRAFT_REQUEST_MACAROON_URL",
                "https://dashboard.snapcraft.io/dev/api/acl/",
            )

    def _get_macaroon(
        self,
        *,
        permissions: Collection[str],
        channels: Collection[str] | None = None,
        packages: Collection[str] | None = None,
        expires: datetime.datetime | None = None,
    ) -> pymacaroons.Macaroon:
        request_object = {
            "permissions": list(permissions),
        }
        if channels is not None:
            request_object["channels"] = list(channels)
        if packages is not None:
            request_object["packages"] = list(packages)
        if expires is not None:
            request_object["expires"] = expires.astimezone(
                datetime.timezone.utc
            ).isoformat()
        macaroon_response = httpx.post(
            self._request_macaroon_url,
            json=request_object,
        )
        macaroon_response.raise_for_status()
        macaroon_token = DeveloperToken.unmarshal(macaroon_response.json())
        return pymacaroons.Macaroon.deserialize(macaroon_token.macaroon)

    @staticmethod
    def _get_login_caveat(
        caveats: list[pymacaroons.Caveat], login_host: str
    ) -> pymacaroons.Caveat:
        match len(caveats):
            case 0:
                raise ValueError("Invalid macaroon: no third-party caveats found")
            case 1:
                return caveats[0]
        caveats = [caveat for caveat in caveats if caveat.location == login_host]
        match len(caveats):
            case 0:
                raise ValueError("Invalid macaroon: no valid login caveats found")
            case 1:
                return caveats[0]
            case _:
                raise ValueError("Invalid macaroon: multiple login caveats found")

    def _discharge_macaroon(
        self,
        macaroon: pymacaroons.Macaroon,
        *,
        email: str,
        password: str,
        otp: str | None = None,
    ) -> pymacaroons.Macaroon:
        login_caveat = self._get_login_caveat(
            macaroon.third_party_caveats(),
            urlparse(self._request_macaroon_url).hostname or "",
        )
        discharge_request = {
            "email": email,
            "password": password,
            "caveat_id": str(login_caveat.caveat_id),
        }
        if otp:
            discharge_request["otp"] = otp
        discharge_response = httpx.post(
            httpx.URL(self._login_url).copy_with(path="/api/v2/tokens/discharge"),
            json=discharge_request,
        )
        discharge_response.raise_for_status()
        return pymacaroons.Macaroon.deserialize(
            discharge_response.json()["discharge_macaroon"]
        )
