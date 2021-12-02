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

import json
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from overrides import overrides
from pymacaroons import Macaroon

from . import endpoints, errors
from .base_client import BaseClient


def _is_needs_refresh_response(response: requests.Response) -> bool:
    return (
        response.status_code == requests.codes.unauthorized  # pylint: disable=no-member
        and response.headers.get("WWW-Authenticate") == "Macaroon needs_refresh=1"
    )


class UbuntuOneStoreClient(BaseClient):
    """Encapsulates API calls for the Snap Store or Charmhub with Ubuntu One."""

    def __init__(
        self,
        *,
        base_url: str,
        auth_url: str,
        endpoints: endpoints.Endpoints,  # pylint: disable=W0621
        application_name: str,
        user_agent: str,
        environment_auth: Optional[str] = None,
    ) -> None:
        super().__init__(
            base_url=base_url,
            endpoints=endpoints,
            application_name=application_name,
            user_agent=user_agent,
            environment_auth=environment_auth,
        )
        self._auth_url = auth_url

    def _get_authorization_header(self) -> str:
        macaroons = json.loads(self._auth.get_credentials())
        root_macaroon = Macaroon.deserialize(macaroons["r"])
        discharged_macaroon = Macaroon.deserialize(macaroons["d"])
        bound_macaroon = root_macaroon.prepare_for_request(
            discharged_macaroon
        ).serialize()
        return f"Macaroon root={macaroons['r']}, discharge={bound_macaroon}"

    def _refresh_token(self) -> None:
        if self._endpoints.tokens_refresh is None:
            raise ValueError("tokens_refresh cannot be None")

        macaroons = json.loads(self._auth.get_credentials())
        response = self.http_client.request(
            "POST",
            self._auth_url + self._endpoints.tokens_refresh,
            json={"discharge_macaroon": macaroons["d"]},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        if not response.ok:
            raise errors.StoreServerError(response)

        macaroons["d"] = response.json()["discharge_macaroon"]

        self._auth.set_credentials(json.dumps(macaroons))

    def _extract_caveat_id(self, root_macaroon):
        macaroon = Macaroon.deserialize(root_macaroon)
        # macaroons are all bytes, never strings
        sso_host = urlparse(self._auth_url).netloc

        for caveat in macaroon.caveats:
            if caveat.location == sso_host:
                return caveat.caveat_id
        raise errors.CraftStoreError("Invalid root macaroon")

    def _discharge(
        self, email: str, password: str, otp: Optional[str], caveat_id
    ) -> str:
        data = dict(email=email, password=password, caveat_id=caveat_id)
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

        return response.json()["discharge_macaroon"]

    def _get_discharged_macaroon(self, root_macaroon: str, **kwargs) -> str:
        email = kwargs["email"]
        password = kwargs["password"]
        otp = kwargs.get("otp")

        cavead_id = self._extract_caveat_id(root_macaroon)
        discharged_macaroon = self._discharge(
            email=email, password=password, otp=otp, caveat_id=cavead_id
        )
        return json.dumps({"r": root_macaroon, "d": discharged_macaroon})

    @overrides
    def request(
        self,
        method: str,
        url: str,
        params: Dict[str, str] = None,
        headers: Dict[str, str] = None,
        **kwargs,
    ) -> requests.Response:
        response = super().request(method, url, params, headers, **kwargs)
        if _is_needs_refresh_response(response):
            self._refresh_token()
            response = super().request(method, url, params, headers, **kwargs)

        return response
