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

"""Craft Store StoreClient."""

from urllib.parse import urlparse

import requests
from overrides import overrides
from pymacaroons import Macaroon  # type: ignore[import]

from . import creds, endpoints, errors
from .base_client import BaseClient


class UbuntuOneStoreClient(BaseClient):
    """Encapsulates API calls for the Snap Store or Charmhub with Ubuntu One."""

    TOKEN_TYPE: str = "u1-macaroon"  # noqa: S105

    def __init__(
        self,
        *,
        base_url: str,
        storage_base_url: str,
        auth_url: str,
        endpoints: endpoints.Endpoints,
        application_name: str,
        user_agent: str,
        environment_auth: str | None = None,
        ephemeral: bool = False,
        file_fallback: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            storage_base_url=storage_base_url,
            endpoints=endpoints,
            application_name=application_name,
            user_agent=user_agent,
            environment_auth=environment_auth,
            ephemeral=ephemeral,
            file_fallback=file_fallback,
        )
        self._auth_url = auth_url

    def _get_authorization_header(self) -> str:
        credentials = self._auth.get_credentials()
        macaroons = creds.unmarshal_u1_credentials(credentials)

        root_macaroon = Macaroon.deserialize(macaroons.root)
        discharged_macaroon = Macaroon.deserialize(macaroons.discharge)
        bound_macaroon = root_macaroon.prepare_for_request(
            discharged_macaroon
        ).serialize()
        return f"Macaroon root={macaroons.root}, discharge={bound_macaroon}"

    def _refresh_token(self) -> None:
        if self._endpoints.tokens_refresh is None:
            raise ValueError("tokens_refresh cannot be None")

        credentials = self._auth.get_credentials()
        macaroons = creds.unmarshal_u1_credentials(credentials)

        response = self.http_client.request(
            "POST",
            self._auth_url + self._endpoints.tokens_refresh,
            json={"discharge_macaroon": macaroons.discharge},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        if not response.ok:
            raise errors.StoreServerError(response)

        macaroons = macaroons.with_discharge(response.json()["discharge_macaroon"])

        new_credentials = creds.marshal_u1_credentials(macaroons)
        self._auth.set_credentials(new_credentials, force=True)

    def _extract_caveat_id(self, root_macaroon: str) -> str:
        macaroon = Macaroon.deserialize(root_macaroon)
        # macaroons are all bytes, never strings
        sso_host = urlparse(self._auth_url).netloc

        for caveat in macaroon.caveats:
            if caveat.location == sso_host:
                return str(caveat.caveat_id)
        raise errors.CraftStoreError("Invalid root macaroon")

    def _discharge(
        self, email: str, password: str, otp: str | None, caveat_id: str
    ) -> str:
        data = {"email": email, "password": password, "caveat_id": caveat_id}
        if otp:
            data["otp"] = otp

        response = self.http_client.request(
            "POST",
            self._auth_url + self._endpoints.tokens_exchange,
            json=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        if not response.ok:
            raise errors.StoreServerError(response)

        return str(response.json()["discharge_macaroon"])

    def _get_discharged_macaroon(  # type: ignore[no-untyped-def]
        self, root_macaroon: str, **kwargs
    ) -> str:
        email = kwargs["email"]
        password = kwargs["password"]
        otp = kwargs.get("otp")

        cavead_id = self._extract_caveat_id(root_macaroon)
        discharged_macaroon = self._discharge(
            email=email, password=password, otp=otp, caveat_id=cavead_id
        )

        u1_macaroon = creds.UbuntuOneMacaroons(r=root_macaroon, d=discharged_macaroon)
        return creds.marshal_u1_credentials(u1_macaroon)

    @overrides
    def request(  # type: ignore[no-untyped-def]
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> requests.Response:
        """Make a request to the store."""
        try:
            response = super().request(method, url, params, headers, **kwargs)
        except errors.StoreServerError as store_error:
            if "macaroon-needs-refresh" in store_error.error_list:
                self._refresh_token()
                response = super().request(method, url, params, headers, **kwargs)
            else:
                raise

        return response
