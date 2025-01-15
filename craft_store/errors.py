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

from __future__ import annotations

import contextlib
import logging
from typing import Any

import httpx
import requests
import urllib3
import urllib3.exceptions
from requests.exceptions import JSONDecodeError

logger = logging.getLogger(__name__)


class CraftStoreError(Exception):
    """Base class error for craft-store."""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        resolution: str | None = None,
        store_errors: StoreErrorList | None = None,
    ) -> None:
        super().__init__(message)
        if store_errors and not details:
            details = str(store_errors)
        self.details = details
        self.resolution = resolution
        self.store_errors = store_errors


class InvalidRequestError(CraftStoreError, ValueError):
    """Error when the request is invalid in a known way."""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        resolution: str | None = None,
    ) -> None:
        super().__init__(message, details, resolution)


class InvalidResponseError(CraftStoreError):
    """Error when the store sends a response that is invalid."""

    def __init__(
        self,
        response: httpx.Response,
        *,
        details: str | None = None,
        resolution: str | None = None,
    ) -> None:
        message = f"Store returned an invalid response (status: {response.status_code})"
        super().__init__(
            message,
            details,
            resolution,
        )


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


class StoreErrorList:
    """Error List returned from the Store."""

    def __len__(self) -> int:
        return len(self._error_list)

    def __str__(self) -> str:
        error_list: list[str] = []
        for error in self._error_list:
            error_list.append(f"- {error['code']}: {error['message']}")
        return "\n".join(error_list).strip()

    def __repr__(self) -> str:
        code_list = []
        for error in self._error_list:
            code = error.get("code")
            if code:
                code_list.append(code)

        return f"<StoreErrorList: {' '.join(code_list)}>"

    def __contains__(self, error_code: str) -> bool:
        return any(error.get("code") == error_code for error in self._error_list)

    def __getitem__(self, error_code: str) -> dict[str, str]:
        for error in self._error_list:
            if error.get("code") == error_code:
                return error

        raise KeyError(error_code)

    def __init__(self, error_list: list[dict[str, str]]) -> None:
        self._error_list = error_list


class StoreServerError(CraftStoreError):
    """Error to raise on infrastructure issues from error codes above ``500``.

    :param response: the response from a :class:`requests.Request`.

    :ivar response: the response from a :class:`requests.Request`.
    :ivar error_list: list of errors returned by the Store :class:`StoreErrorList`.
    """

    def _get_raw_error_list(self) -> list[dict[str, str]]:
        response_json: dict[str, Any] = self.response.json()
        try:
            # Charmhub uses error-list.
            error_list: list[dict[str, str]] = response_json["error-list"]
        except KeyError:
            # Snap Store uses error_list.
            error_list = response_json["error_list"]

        return error_list

    def __init__(self, response: requests.Response | httpx.Response) -> None:
        self.response = response

        try:
            raw_error_list: list[dict[str, str]] = self._get_raw_error_list()
        except (KeyError, JSONDecodeError):
            raw_error_list = []

        self.error_list = StoreErrorList(raw_error_list)

        message: str | None = None
        if self.error_list:
            with contextlib.suppress(KeyError):
                message = "Store operation failed:\n" + str(self.error_list)
        if message is None:
            if isinstance(response, httpx.Response):
                reason = response.reason_phrase
            else:
                reason = response.reason
            message = (
                "Issue encountered while processing your request: "
                f"[{response.status_code}] {reason}."
            )

        super().__init__(message)


class CredentialsAlreadyAvailable(CraftStoreError):  # noqa: N818
    """Error raised when credentials are already found in the keyring."""

    def __init__(self, application: str, host: str) -> None:
        super().__init__(f"Credentials found for {application!r} on {host!r}.")


class CredentialsUnavailable(CraftStoreError):  # noqa: N818
    """Error raised when credentials are not found in the keyring."""

    def __init__(self, application: str, host: str) -> None:
        super().__init__(f"No credentials found for {application!r} on {host!r}.")


class CredentialsNotParseable(CraftStoreError):  # noqa: N818
    """Error raised when credentials are not parseable."""

    def __init__(self, msg: str = "Expected base64 encoded credentials") -> None:
        super().__init__(f"Credentials could not be parsed. {msg}.")


class NoKeyringError(CraftStoreError):
    """Error raised when no keyring can be used."""

    def __init__(self) -> None:
        super().__init__("No keyring found to store or retrieve credentials from.")


class KeyringUnlockError(CraftStoreError):
    """Error raised when keyring unlocking fails."""

    def __init__(self) -> None:
        super().__init__(
            "Failed to unlock the keyring.",
            resolution="Make sure the password is correct and the keyring is available.",
        )


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


class AuthTokenUnavailableError(CraftStoreError):
    """Raised when an authorization token is not available."""
