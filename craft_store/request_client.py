# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
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

"""Client for making requests towards publisher gateway."""

import contextlib
from collections.abc import Generator
from enum import Enum
from json import JSONDecodeError
from logging import getLogger
from typing import Any, Literal

import httpx

from craft_store import auth, creds, errors

logger = getLogger(__name__)


class DeveloperTokenAuth(httpx.Auth):
    """Request authentication using developer token."""

    def __init__(
        self,
        *,
        auth: auth.Auth,
        auth_type: Literal["bearer", "macaroon"] = "bearer",
    ) -> None:
        self._auth = auth
        self._auth_type = auth_type

    def auth_flow(
        self,
        request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Update request to include Authorization header."""
        logger.debug("Adding developer token to authorize request")
        if self._developer_token is None:
            self.get_token_from_keyring()

        self._update_headers(request)
        yield request

    def get_token_from_keyring(self) -> None:
        """Get token stored in the credentials storage."""
        logger.debug("Getting developer token from credential storage")
        dev_token = creds.DeveloperToken.from_json_string(self._auth.get_credentials())
        self._developer_token = dev_token.macaroon

    def _update_headers(self, request: httpx.Request) -> None:
        """Add token to the request."""
        logger.debug("Adding ephemeral token to request headers")
        if self._developer_token is None:
            raise errors.DeveloperTokenUnavailableError(
                message="Developer token is not available"
            )
        request.headers["Authorization"] = self._format_auth_header()

    def _format_auth_header(self) -> str:
        if self._auth_type == "bearer":
            return f"Bearer {self._developer_token}"
        return f"Macaroon {self._developer_token}"


class StoreOperationStatus(str, Enum):
    """Class that reflects status of ongoing task."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RUNNING = "running"
    WAITING = "waiting"

    def is_ongoing(self) -> bool:
        """Check if task is still running."""
        return self in (
            StoreOperationStatus.WAITING,
            StoreOperationStatus.RUNNING,
        )


class StoreConnectionError(errors.CraftStoreError):
    """Error raised if request cannot be issued."""


class AuthenticationError(errors.CraftStoreError):
    """Error raised if request is unauthenticated."""


class StoreRequestProcessingError(errors.CraftStoreError):
    """Error to raise when store returns non-ok response.

    :param response: the response from a :class:`httpx.Request`.

    :ivar response: the response from a :class:`httpx.Request`.
    :ivar error_list: list of errors returned by the Store :class:`StoreErrorList`.
    """

    def __init__(self, response: httpx.Response) -> None:
        self.response = response

        try:
            raw_error_list: list[dict[str, str]] = self._get_raw_error_list()
        except (KeyError, JSONDecodeError):
            raw_error_list = []

        self.error_list = errors.StoreErrorList(raw_error_list)

        message: str | None = None
        if self.error_list:
            with contextlib.suppress(KeyError):
                message = "Store operation failed:\n" + str(self.error_list)
        if message is None:
            message = (
                "Issue encountered while processing your request: "
                f"[{response.status_code}] {response.reason_phrase}."
            )

        super().__init__(message)

    def _get_raw_error_list(self) -> list[dict[str, str]]:
        response_json: dict[str, Any] = self.response.json()
        try:
            # Charmhub uses error-list.
            error_list: list[dict[str, str]] = response_json["error-list"]
        except KeyError:
            # Snap Store uses error_list.
            error_list = response_json["error_list"]

        return error_list


class StoreRequestClient:
    """Client which talks with the Store through API."""

    def __init__(
        self,
        *,
        auth: httpx.Auth,
        timeout: float = 30.0,
    ) -> None:
        self._client = httpx.Client(auth=auth, timeout=timeout)

    def get(
        self,
        url: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> httpx.Response:
        """Sent GET request to the Store."""
        return self.request("GET", url, **kwargs)

    def post(
        self,
        url: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> httpx.Response:
        """Sent POST request to the Store."""
        return self.request("POST", url, **kwargs)

    def put(
        self,
        url: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> httpx.Response:
        """Sent DELETE request to the Store."""
        return self.request("PUT", url, **kwargs)

    def delete(
        self,
        url: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> httpx.Response:
        """Sent DELETE request to the Store."""
        return self.request("DELETE", url, **kwargs)

    def request(
        self,
        http_method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        check: bool = True,
        check_store_task_status: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> httpx.Response:
        """Issue HTTP reqeust agains given URL."""
        if headers is None:
            headers = {}
        try:
            logger.debug("Calling method %s on endpoint %s", http_method, url)
            logger.debug("with query parameters: %s", kwargs.get("params"))
            logger.debug("with data: %s", kwargs.get("json"))
            response = self._client.request(
                http_method,
                url,
                headers=headers,
                **kwargs,
            )
        except httpx.HTTPError as err:
            logger.debug(
                "Error occurred when processing request to %r",
                err.request.url,
            )
            raise StoreConnectionError(
                message="Error response received from store",
                resolution="Check your network connectivity and try again.",
            ) from err
        else:
            if check:
                self._check_response_code(response)

            # TODO: check if we want that as a part of API
            # or handle it in service directly
            if check_store_task_status:
                self._check_store_task_status(response)

            return response

    def _check_response_code(self, response: httpx.Response) -> None:
        """Check if requests has a succesfull HTTP code."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            logger.warning(
                "Error response (%d) received from store while processing request %r",
                error.response.status_code,
                error.request.url,
            )
            if error.response.status_code == httpx.codes.UNAUTHORIZED:
                raise AuthenticationError(
                    message="Not authorized to issue this request",
                    resolution="Check your credentials and/or permissions before trying again",
                ) from error
            raise StoreRequestProcessingError(response=error.response) from error

    def _check_store_task_status(self, response: httpx.Response) -> None:
        """Check if store task status is failed."""
        try:
            status = StoreOperationStatus(response.json().get("status"))
        except (JSONDecodeError, ValueError) as error:
            raise StoreRequestProcessingError(response=response) from error

        else:
            if status == StoreOperationStatus.FAILED:
                raise StoreRequestProcessingError(response)
