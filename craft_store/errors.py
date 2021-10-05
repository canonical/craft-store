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

"""Craft Store errors."""

import contextlib
import logging
from typing import Optional

import requests
import urllib3  # type: ignore

logger = logging.getLogger(__name__)


class CraftStoreError(Exception):
    """Base class error for craft-store."""

    def __init__(self, message: str, resolution: Optional[str] = None) -> None:
        super().__init__(message)
        self.resolution = resolution


class NetworkError(CraftStoreError):
    """Error to raise on network or infrastructure issues.

    The original exception is used to potentially craft a user friendly
    error message to be used for :attr:`.brief`.

    :param exception: original exception raised.

    :ivar exception: original exception raised.
    """

    def __init__(self, exception: Exception) -> None:
        message = str(exception)
        with contextlib.suppress(IndexError):
            if isinstance(exception.args[0], urllib3.exceptions.MaxRetryError):
                message = "Maximum retries exceeded trying to reach the store."

        super().__init__(message)


class StoreServerError(CraftStoreError):
    """Error to raise on infrastructure issues from error codes above ``500``.

    :param response: the response from a :class:`requests.Request`.

    :ivar response: the response from a :class:`requests.Request`.
    """

    def __init__(self, response: requests.Response) -> None:
        self.response = response

        super().__init__(
            "Issue encountered while processing your request: "
            f"[{response.status_code}] {response.reason}."
        )


class NotLoggedIn(CraftStoreError):
    """Error raised when credentials are not found in the keyring."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Not logged in: {message}.")


class CandidTokenTimeoutError(CraftStoreError):
    """Error raised when timeout is reached trying to discharge a macaroon."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Timed out waiting for token response from {url!r}.")


class CandidTokenKindError(CraftStoreError):
    """Error raised when the token kind is missing from the discharged macaroon."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Empty token kind returned from {url!r}.")


class CandidTokenValueError(CraftStoreError):
    """Error raised when the token value is missing from the discharged macaroon."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Empty token value returned from {url!r}.")
