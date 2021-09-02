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
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter, Retry

from . import errors

logger = logging.getLogger(__name__)


class HTTPClient:
    """Generic HTTP Client to communicate with Canonical's Developer Gateway.

    This client has a request's like interface, it creates a requess.Session
    on initialization to handle retries over HTTP and HTTPS requests.

    The default number of retries is set to 5 and can be overridden through
    the ``CRAFT_STORE_RETRIES`` environment variable.

    The backoff factor has a default of 2 and can be overridden with the
    ``CRAFT_STORE_BACKOFF`` environment variable.

    Retires are done for the following return codes: ``104``, ``500``, ``502``,
    ``503`` and ``504``.

    :ivar user_agent: User-Agent header to identify the client.
    """

    def __init__(self, *, user_agent: str) -> None:
        """Initialize and HTTPClient with a given user_agent.

        :param user_agent: User-Agent header to identify the client.
        """
        self._session = requests.Session()
        self.user_agent = user_agent

        try:
            total = int(os.environ.get("CRAFT_STORE_RETRIES", 10))
        except ValueError:
            total = 10
            logger.debug(
                "CRAFT_STORE_RETRIES is not se to an integer, using default of %r.",
                total,
            )

        try:
            backoff = int(os.environ.get("CRAFT_STORE_BACKOFF", 2))
        except ValueError:
            backoff = 2
            logger.debug(
                "CRAFT_STORE_BACKOFF is not se to an integer, using default of %r.",
                backoff,
            )

        # Setup max retries for all store URLs and the CDN
        retries = Retry(
            total=total,
            backoff_factor=backoff,
            status_forcelist=[104, 500, 502, 503, 504],
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

        :raises errors.StoreNetworkError: for responses above error code ``500``.

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

        # Handle 5XX responses generically right here, so the callers don't
        # need to worry about it.
        if response.status_code >= 500:
            raise errors.StoreServerError(response)

        return response
