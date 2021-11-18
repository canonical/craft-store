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
from typing import Any, Dict, Optional, Sequence
from urllib.parse import urlparse

import requests
from macaroonbakery import bakery, httpbakery
from pymacaroons.serializers import json_serializer

from . import endpoints, errors
from .auth import Auth
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


class StoreClient(HTTPClient):
    """Encapsulates API calls for the Snap Store or Charmhub."""

    def __init__(
        self,
        *,
        base_url: str,
        endpoints: endpoints.Endpoints,  # pylint: disable=W0621
        application_name: str,
        user_agent: str,
        environment_auth: Optional[str] = None,
    ) -> None:
        """Initialize the Store Client.

        :param base_url: the base url of the API endpoint.
        :param endpoints: :data:`.endpoints.CHARMHUB` or :data:`.endpoints.SNAP_STORE`.
        :param application_name: the name application using this class, used for the keyring.
        :param user_agent: User-Agent header to use for HTTP(s) requests.
        :param environment_auth: environment variable to use for credentials.
        """
        super().__init__(user_agent=user_agent)

        self._bakery_client = httpbakery.Client(
            interaction_methods=[WebBrowserWaitingInteractor(user_agent=user_agent)]
        )
        self._base_url = base_url
        self._store_host = urlparse(base_url).netloc
        self._endpoints = endpoints

        self._auth = Auth(application_name, base_url, environment_auth=environment_auth)

    def _get_macaroon(self, token_request: Dict[str, Any]) -> str:
        token_response = super().request(
            "POST",
            self._base_url + self._endpoints.tokens,
            json=token_request,
        )

        return token_response.json()["macaroon"]

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
        token_exchange_response = super().request(
            "POST",
            self._base_url + self._endpoints.tokens_exchange,
            headers={"Macaroons": candid_discharged_macaroon},
            json={},
        )

        return token_exchange_response.json()["macaroon"]

    def login(
        self,
        *,
        permissions: Sequence[str],
        description: str,
        ttl: int,
        packages: Optional[Sequence[endpoints.Package]] = None,
        channels: Optional[Sequence[str]] = None,
    ) -> str:
        """Obtain credentials to perform authenticated requests.

        Credentials are stored on the systems keyring, handled by
        :data:`craft_store.auth.Auth`.

        The list of permissions to select from can be referred to on
        :data:`craft_store.attenuations`.

        The login process requires 3 steps:

        - request an initial macaroon on :attr:`.endpoints.Endpoints.tokens`.
        - discharge that macaroon using Candid
        - send the discharge macaroon to :attr:`.endpoints.Endpoints.tokens_exchange`
          to obtain final authorization of the macaroon

        This last macaroon is stored into the systems keyring to
        perform authenticated requests.

        :param permissions: Set of permissions to grant the login.
        :param description: Client description to refer to from the Store.
        :param ttl: time to live for the credential, in other words, how
                    long until it expires, expressed in seconds.
        :param packages: Sequence of packages to limit the credentials to.
        :param channels: Sequence of channel names to limit the credentials to.
        """
        token_request = self._endpoints.get_token_request(
            permissions=permissions,
            description=description,
            ttl=ttl,
            packages=packages,
            channels=channels,
        )

        macaroon = self._get_macaroon(token_request)
        candid_discharged_macaroon = self._candid_discharge(macaroon)
        store_authorized_macaroon = self._authorize_token(candid_discharged_macaroon)

        # Save the authorization token.
        self._auth.set_credentials(store_authorized_macaroon)

        return self._auth.encode_credentials(store_authorized_macaroon)

    def request(
        self,
        method: str,
        url: str,
        params: Dict[str, str] = None,
        headers: Dict[str, str] = None,
        **kwargs,
    ) -> requests.Response:
        """Perform an authenticated request if auth_headers are True.

        :param method: HTTP method used for the request.
        :param url: URL to request with method.
        :param params: Query parameters to be sent along with the request.
        :param headers: Headers to be sent along with the request.

        :raises errors.StoreServerError: for error responses.
        :raises errors.NetworkError: for lower level network issues.
        :raises errors.NotLoggedIn: if not logged in.

        :return: Response from the request.
        """
        if headers is None:
            headers = {}

        auth = self._auth.get_credentials()
        headers["Authorization"] = f"Macaroon {auth}"

        return super().request(
            method,
            url,
            params=params,
            headers=headers,
            **kwargs,
        )

    def whoami(self) -> Dict[str, Any]:
        """Return whoami json data queyring :attr:`.endpoints.Endpoints.whoami`."""
        return self.request("GET", self._base_url + self._endpoints.whoami).json()

    def logout(self) -> None:
        """Clear credentials.

        :raises errors.NotLoggedIn: if not logged in.
        """
        self._auth.del_credentials()
