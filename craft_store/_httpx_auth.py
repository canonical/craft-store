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
