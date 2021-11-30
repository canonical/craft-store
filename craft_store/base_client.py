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

"""Craft Store BaseClient."""

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional, Sequence
from urllib.parse import urlparse

import requests

from . import endpoints
from .auth import Auth
from .http_client import HTTPClient


class BaseClient(metaclass=ABCMeta):
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
        self.http_client = HTTPClient(user_agent=user_agent)

        self._base_url = base_url
        self._store_host = urlparse(base_url).netloc
        self._endpoints = endpoints

        self._auth = Auth(application_name, base_url, environment_auth=environment_auth)

    @abstractmethod
    def _get_discharged_macaroon(self, root_macaroon: str, **kwargs) -> str:
        """Return a discharged macaroon ready to use in an Authorization header."""

    @abstractmethod
    def _get_authorization_header(self) -> str:
        """Return the authorization header content to use."""

    def _get_macaroon(self, token_request: Dict[str, Any]) -> str:
        token_response = self.http_client.request(
            "POST",
            self._base_url + self._endpoints.tokens,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=token_request,
        )

        return token_response.json()["macaroon"]

    def login(
        self,
        *,
        permissions: Sequence[str],
        description: str,
        ttl: int,
        packages: Optional[Sequence[endpoints.Package]] = None,
        channels: Optional[Sequence[str]] = None,
        **kwargs,
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
        store_authorized_macaroon = self._get_discharged_macaroon(macaroon, **kwargs)

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

        headers["Authorization"] = self._get_authorization_header()

        return self.http_client.request(
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
