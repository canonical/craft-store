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

import base64
import json
from typing import Optional

from macaroonbakery import bakery, httpbakery
from overrides import overrides
from pymacaroons.serializers import json_serializer

from . import endpoints, errors
from .base_client import BaseClient
from .http_client import HTTPClient


def _macaroon_to_json_string(macaroon) -> str:
    return macaroon.serialize(json_serializer.JsonSerializer())


class WebBrowserWaitingInteractor(httpbakery.WebBrowserInteractor):
    """WebBrowserInteractor implementation using HTTPClient.

    Waiting for a token is implemented using HTTPClient which mounts
    a session with backoff retries.

    Better exception classes and messages are  provided to handle errors.
    """

    def __init__(self, user_agent: str) -> None:
        super().__init__()
        self.user_agent = user_agent

    # TODO: transfer implementation to macaroonbakery.
    def _wait_for_token(self, ctx, wait_token_url):
        request_client = HTTPClient(user_agent=self.user_agent)
        resp = request_client.request("GET", wait_token_url)
        if resp.status_code != 200:
            raise errors.CandidTokenTimeoutError(url=wait_token_url)
        json_resp = resp.json()
        kind = json_resp.get("kind")
        if kind is None:
            raise errors.CandidTokenKindError(url=wait_token_url)
        token_val = json_resp.get("token")
        if token_val is None:
            token_val = json_resp.get("token64")
            if token_val is None:
                raise errors.CandidTokenValueError(url=wait_token_url)
            token_val = base64.b64decode(token_val)
        return httpbakery._interactor.DischargeToken(  # pylint: disable=W0212
            kind=kind, value=token_val
        )


class StoreClient(BaseClient):
    """Encapsulates API calls for the Snap Store or Charmhub."""

    @overrides
    def __init__(
        self,
        *,
        base_url: str,
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

        self._bakery_client = httpbakery.Client(
            interaction_methods=[WebBrowserWaitingInteractor(user_agent=user_agent)]
        )

    def _get_authorization_header(self) -> str:
        auth = self._auth.get_credentials()
        return f"Macaroon {auth}"

    def _candid_discharge(self, macaroon: str) -> str:
        bakery_macaroon = bakery.Macaroon.from_dict(json.loads(macaroon))
        discharges = bakery.discharge_all(
            bakery_macaroon, self._bakery_client.acquire_discharge
        )

        # serialize macaroons the bakery-way
        discharged_macaroons = (
            "[" + ",".join(map(_macaroon_to_json_string, discharges)) + "]"
        )

        return base64.urlsafe_b64encode(discharged_macaroons.encode()).decode("ascii")

    def _authorize_token(self, candid_discharged_macaroon: str) -> str:
        token_exchange_response = self.http_client.request(
            "POST",
            self._base_url + self._endpoints.tokens_exchange,
            headers={"Macaroons": candid_discharged_macaroon},
            json={},
        )

        return token_exchange_response.json()["macaroon"]

    def _get_discharged_macaroon(self, root_macaroon: str, **kwargs) -> str:
        candid_discharged_macaroon = self._candid_discharge(root_macaroon)
        return self._authorize_token(candid_discharged_macaroon)
