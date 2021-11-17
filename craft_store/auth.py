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

"""Craft Store Authentication Store."""

import base64
import logging
import os
from typing import Dict, Optional, Tuple

import keyring
import keyring.backend
import keyring.errors

from . import errors

logger = logging.getLogger(__name__)


class MemoryKeyring(keyring.backend.KeyringBackend):
    """A keyring that stores credentials in a dictionary."""

    priority = 1  # type: ignore

    def __init__(self) -> None:
        super().__init__()

        self._credentials: Dict[Tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        """Set the service password for username in memory."""
        self._credentials[service, username] = password

    def get_password(self, service: str, username: str) -> Optional[str]:
        """Get the service password for username from memory."""
        return self._credentials.get((service, username))

    def delete_password(self, service: str, username: str) -> None:
        """Delete the service password for username from memory."""
        try:
            del self._credentials[service, username]
        except KeyError as key_error:
            raise keyring.errors.PasswordDeleteError() from key_error


class Auth:
    """Auth wraps around the keyring to store credentials.

    The application_name and host are used as key/values in the keyring to set,
    get and delete credentials.

    If environment_auth is set on initialization of this class, then a
    :attr:`MemoryKeyring` is setup in lieu of the system one.

    Credentials are base64 encoded into the keyring and decoded on
    retrieval.

    :ivar application_name: name of the application using this library.
    :ivar host: specific host for the store used.
    """

    def __init__(
        self,
        application_name: str,
        host: str,
        environment_auth: Optional[str] = None,
    ) -> None:
        """Initialize Auth.

        :param application_name: name of the application using this library.
        :param host: specific host for the store used.
        :param environment_auth: environment variable used for authentication.
        """
        self.application_name = application_name
        self.host = host

        environment_auth_value = None
        if environment_auth:
            environment_auth_value = os.getenv(environment_auth)

        if environment_auth_value:
            keyring.set_keyring(MemoryKeyring())

        self._keyring = keyring.get_keyring()

        if environment_auth_value:
            self.set_credentials(self.decode_credentials(environment_auth_value))

    @staticmethod
    def decode_credentials(encoded_credentials: str) -> str:
        """Decode base64 encoded credentials."""
        return base64.b64decode(encoded_credentials).decode()

    @staticmethod
    def encode_credentials(credentials: str) -> str:
        """Encode credentials to base64."""
        return base64.b64encode(credentials.encode()).decode()

    def set_credentials(self, credentials: str) -> None:
        """Store credentials in the keyring.

        :param credentials: token to store.
        """
        logger.debug(
            "Storing credentials for %r on %r in keyring %r.",
            self.application_name,
            self.host,
            self._keyring.name,
        )
        encoded_credentials = self.encode_credentials(credentials)
        self._keyring.set_password(
            self.application_name, self.host, encoded_credentials
        )

    def get_credentials(self) -> str:
        """Retrieve credentials from the keyring."""
        logger.debug(
            "Retrieving credentials for %r on %r from keyring %r.",
            self.application_name,
            self.host,
            self._keyring.name,
        )

        try:
            encoded_credentials_string = self._keyring.get_password(
                self.application_name, self.host
            )
        except Exception as unknown_error:
            logger.debug(
                "Unhandled exception raised when retrieving credentials: %r",
                unknown_error,
            )
            raise errors.NotLoggedIn() from unknown_error

        if encoded_credentials_string is None:
            logger.debug("Credentials not found in the keyring %r", self._keyring.name)
            raise errors.NotLoggedIn()
        credentials = self.decode_credentials(encoded_credentials_string)
        return credentials

    def del_credentials(self) -> None:
        """Delete credentials from the keyring."""
        # Try to get the credentials first to see if there are any,
        # this is to provide an easier troubleshooting experience.
        self.get_credentials()

        logger.debug(
            "Deleting credentials for %r on %r from keyring %r.",
            self.application_name,
            self.host,
            self._keyring.name,
        )
        self._keyring.delete_password(self.application_name, self.host)
