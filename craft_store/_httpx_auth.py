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

"""Craft Store Authentication Store."""

import abc
import logging
from collections.abc import Generator
from typing import Literal

import httpx
from pymacaroons import Macaroon  # type: ignore[import-untyped]
from typing_extensions import override

from craft_store import auth, creds, errors

logger = logging.getLogger(__name__)


class _TokenAuth(httpx.Auth, metaclass=abc.ABCMeta):
    """Base class for httpx token-based authenticators."""

    def __init__(
        self, *, auth: auth.Auth, auth_type: Literal["bearer", "macaroon"] = "bearer"
    ) -> None:
        super().__init__()
        self._token: str | None = None
        self._auth = auth
        self._auth_type = auth_type

    @override
    def auth_flow(
        self,
        request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Update request to include Authorization header."""
        if self._token is None:
            logger.debug("Getting token from keyring")
            self._token = self.get_token_from_keyring()

        self._update_headers(request)
        yield request

    @abc.abstractmethod
    def get_token_from_keyring(self) -> str:
        """Get token stored in the credentials storage."""

    def _update_headers(self, request: httpx.Request) -> None:
        """Add token to the request."""
        logger.debug("Adding ephemeral token to request headers")
        if self._token is None:
            raise errors.AuthTokenUnavailableError(message="Token is not available")
        request.headers["Authorization"] = self._format_auth_header()

    def _format_auth_header(self) -> str:
        if self._auth_type == "bearer":
            return f"Bearer {self._token}"
        return f"Macaroon {self._token}"


class CandidAuth(_TokenAuth):
    """Candid based authentication class for httpx store clients."""

    def __init__(
        self, *, auth: auth.Auth, auth_type: Literal["bearer", "macaroon"] = "macaroon"
    ) -> None:
        super().__init__(auth=auth, auth_type=auth_type)

    def get_token_from_keyring(self) -> str:
        """Get token stored in the credentials storage."""
        logger.debug("Getting candid from credential storage")
        return creds.unmarshal_candid_credentials(self._auth.get_credentials())


class DeveloperTokenAuth(_TokenAuth):
    """Developer token based authentication class for httpx store clients."""

    def get_token_from_keyring(self) -> str:
        """Get token stored in the credentials storage."""
        logger.debug("Getting developer token from credential storage")
        return creds.DeveloperToken.model_validate_json(
            self._auth.get_credentials()
        ).macaroon


class UbuntuOneAuth(httpx.Auth):
    """Ubuntu One macaroon auth class for httpx store clients."""

    def __init__(
        self,
        *,
        auth: auth.Auth,
        api_base_url: str,
        client_description: str = "craft-store",
    ) -> None:
        self._auth = auth
        self._api_base_url = api_base_url
        self._client_description = client_description
        self._token: str | None = None

    def auth_flow(
        self,
        request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        if self._token is None:
            logger.debug("Getting Ubuntu One macaroon from keyring")
            self._token = self.get_token_from_keyring()

        request.headers["Authorization"] = self._format_auth_header()
        yield request

    def _format_auth_header(self) -> str:
        if self._token is None:
            raise errors.AuthTokenUnavailableError(message="Token is not available")
        return f"Macaroon {self._token}"

    def get_token_from_keyring(self) -> str:
        """Exchange Ubuntu One macaroons stored in the credentials storage.

        On first call, exchanges the macaroons for a store token and caches it.
        On subsequent calls, uses the cached token instead of re-exchanging.
        """
        logger.debug("Getting credentials from storage")
        stored_creds = self._auth.get_credentials()

        # Check if this is already a cached store token (not macaroons)
        # A cached token will be a simple string, while macaroons are JSON with 'r' and 'd' keys
        try:
            creds_dict = creds.unmarshal_u1_credentials(stored_creds)
            # If we get here, it's valid macaroons in dict format, so exchange them
            logger.debug("Found macaroons; attempting to exchange for store token")
            macaroons = creds_dict
        except errors.CredentialsNotParseable:
            # If unmarshaling fails, treat it as a cached store token
            logger.debug("Using cached store token from credentials")
            return stored_creds

        root_macaroon = Macaroon.deserialize(macaroons.root)
        discharge_macaroon = Macaroon.deserialize(macaroons.discharge)
        bound_discharge = root_macaroon.prepare_for_request(
            discharge_macaroon
        ).serialize()
        response = httpx.post(
            f"{self._api_base_url}/v1/tokens/usso/exchange",
            headers={
                "Authorization": (
                    f"Macaroon root={macaroons.root}, discharge={bound_discharge}"
                )
            },
            json={"client-description": self._client_description},
            timeout=60.0,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            error_message = self._extract_error_message(exc)
            if error_message:
                raise errors.CraftStoreError(
                    "Ubuntu One macaroon exchange failed.",
                    details=error_message,
                ) from exc
            raise
        try:
            store_token = str(response.json()["macaroon"])
        except (TypeError, KeyError) as exc:
            raise errors.InvalidResponseError(
                response,
                details="Missing 'macaroon' in /v1/tokens/usso/exchange response",
            ) from exc

        # Cache the exchanged token by storing it as the new credentials
        self._cache_exchange_token(store_token)
        return store_token

    def _cache_exchange_token(self, token: str) -> None:
        """Cache the exchanged token by storing it as credentials."""
        try:
            self._auth.set_credentials(token, force=True)
            logger.debug("Cached store token in keyring for future use")
        except Exception as exc:
            logger.warning("Failed to cache store token: %s", exc)
            raise

    @staticmethod
    def _extract_error_message(exc: httpx.HTTPStatusError) -> str | None:
        """Extract error message from response body if available."""
        try:
            response_json = exc.response.json()
        except ValueError:
            return None

        # Try error_list format
        error_list = response_json.get("error_list") or response_json.get("error-list")
        if isinstance(error_list, list) and error_list:
            for error in error_list:
                if isinstance(error, dict):
                    message = error.get("message")
                    if message:
                        return str(message)

        # Try direct message field
        message = response_json.get("message")
        if message:
            return str(message)

        return None
