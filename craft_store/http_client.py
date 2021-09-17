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

"""Craft Store HTTPClient."""

import logging
import os
from typing import Dict, Optional, Union

import requests
from requests.adapters import HTTPAdapter, Retry

from . import errors

logger = logging.getLogger(__name__)


REQUEST_TOTAL_RETRIES = 8
"""Amount of retries for a request."""
REQUEST_BACKOFF = 0.2
"""Backoff before retrying a request."""


def _get_retry_value(
    environment_var: str, default_value: Union[int, float]
) -> Union[int, float]:
    """Return the backoff to use in HTTPClient."""
    environment_value = os.getenv(environment_var)
    if environment_value is None:
        return default_value

    try:
        value = int(environment_value)
    except ValueError:
        logger.debug(
            "%r set to invalid value %r, setting to %r.",
            environment_var,
            environment_value,
            default_value,
        )
        return default_value

    if value < 0:
        logger.debug(
            "%r set to non positive value %r, setting to %r.",
            environment_var,
            value,
            default_value,
        )
        return default_value

    return value


class HTTPClient:
    """Generic HTTP Client to communicate with Canonical's Developer Gateway.

    This client has a requests like interface, it creates a requests.Session
    on initialization to handle retries over HTTP and HTTPS requests.

    The default number of retries is set in :data:`.REQUEST_TOTAL_RETRIES` and can
    be overridden with the ``CRAFT_STORE_RETRIES`` environment variable.

    The backoff factor has a default set in :data:`.REQUEST_BACKOFF` and can be
    overridden with the ``CRAFT_STORE_BACKOFF`` environment variable.

    Retries are done for the following return codes: ``500``, ``502``, ``503``
    and ``504``.

    :ivar user_agent: User-Agent header to identify the client.
    """

    def __init__(self, *, user_agent: str) -> None:
        """Initialize an HTTPClient with a given user_agent.

        :param user_agent: User-Agent header to identify the client.
        """
        self._session = requests.Session()
        self.user_agent = user_agent

        # Setup max retries for all store URLs and the CDN
        retries = Retry(
            total=_get_retry_value("CRAFT_STORE_RETRIES", REQUEST_TOTAL_RETRIES),
            backoff_factor=_get_retry_value("CRAFT_STORE_BACKOFF", REQUEST_BACKOFF),
            status_forcelist=[500, 502, 503, 504],
        )
        http_adapter = HTTPAdapter(max_retries=retries)
        self._session.mount("http://", http_adapter)
        self._session.mount("https://", http_adapter)

    def get(self, *args, **kwargs) -> requests.Response:
        """Perform an HTTP GET request."""
        return self.request("GET", *args, **kwargs)

    def post(self, *args, **kwargs) -> requests.Response:
        """Perform an HTTP POST request."""
        return self.request("POST", *args, **kwargs)

    def put(self, *args, **kwargs) -> requests.Response:
        """Perform an HTTP PUT request."""
        return self.request("PUT", *args, **kwargs)

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        """Send a request to url.

        :attr:`.user_agent` is set as part of the headers for the request.
        All requests are logged through a debug logs, headers matching
        Authorization and Macaroons have their value replaced.

        :param method: HTTP method used for the request.
        :param url: URL to request with method.
        :param params: Query parameters to be sent along with the request.
        :param headers: Headers to be sent along with the request.

        :raises errors.StoreServerError: for error responses.
        :raises errors.NetworkError: for lower level network issues.

        :return: Response from the request.
        """
        if headers:
            headers["User-Agent"] = self.user_agent
        else:
            headers = {"User-Agent": self.user_agent}

        debug_headers = headers.copy()
        if debug_headers.get("Authorization"):
            debug_headers["Authorization"] = "<macaroon>"
        if debug_headers.get("Macaroons"):
            debug_headers["Macaroons"] = "<macaroon>"
        logger.debug(
            "HTTP %r for %r with params %r and headers %r",
            method,
            url,
            params,
            debug_headers,
        )
        try:
            response = self._session.request(
                method, url, headers=headers, params=params, **kwargs
            )
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.RetryError,
        ) as error:
            raise errors.NetworkError(error) from error

        if not response.ok:
            raise errors.StoreServerError(response)

        return response
