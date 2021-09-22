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

import keyring
import keyring.errors

from . import errors

logger = logging.getLogger(__name__)


class Auth:
    """Auth wraps around the keyring to store credentials.

    The application_name and host are used as key/values in the keyring to set,
    get and delete credentials.

    Credentials are base64 encoded into the keyring and decoded on retrieval.

    :ivar application_name: name of the application using this library.
    :ivar host: specific host for the store used.
    """

    def __init__(self, application_name: str, host: str) -> None:
        """Initialize Auth.

        :param application_name: name of the application using this library.
        :param host: specific host for the store used.
        """
        self.application_name = application_name
        self.host = host

    def set_credentials(self, credentials: str) -> None:
        """Store credentials in the keyring.

        :param credentials: token to store.
        """
        logger.debug(
            "Storing credentials for %r on %r in keyring.",
            self.application_name,
            self.host,
        )
        encoded_credentials = base64.b64encode(credentials.encode())
        keyring.set_password(
            self.application_name, self.host, encoded_credentials.decode()
        )

    def get_credentials(self) -> str:
        """Retrieve credentials from the keyring."""
        logger.debug(
            "Retrieving credentials for %r on %r from keyring.",
            self.application_name,
            self.host,
        )
        encoded_credentials_string = keyring.get_password(
            self.application_name, self.host
        )
        if encoded_credentials_string is None:
            keyring_name = keyring.get_keyring().name
            raise errors.NotLoggedIn(
                f"credentials not found in the keyring {keyring_name!s}"
            )
        credentials = base64.b64decode(encoded_credentials_string).decode()
        return credentials

    def del_credentials(self) -> None:
        """Delete credentials from the keyring."""
        logger.debug(
            "Deleting credentials for %r on %r from keyring.",
            self.application_name,
            self.host,
        )
        try:
            keyring.delete_password(self.application_name, self.host)
        except keyring.errors.PasswordDeleteError as delete_error:
            keyring_name = keyring.get_keyring().name
            raise errors.NotLoggedIn(
                f"credentials not found in the keyring {keyring_name!s}"
            ) from delete_error
