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
import binascii
import json
import logging
import os
import sys
from pathlib import Path
from typing import cast

import keyring
import keyring.backend
import keyring.backends.fail
import keyring.errors
from jaraco.classes import properties
from xdg import BaseDirectory  # type: ignore[import-untyped]

from . import errors

# workaround to prevent legacy provider loading in focal
os.environ["CRYPTOGRAPHY_OPENSSL_NO_LEGACY"] = "1"
from keyring.backends import SecretService

logger = logging.getLogger(__name__)


if sys.platform == "linux":
    from secretstorage.exceptions import SecretServiceNotAvailableException

    KEYRING_EXCEPTIONS = (keyring.errors.InitError, SecretServiceNotAvailableException)
else:
    KEYRING_EXCEPTIONS = (keyring.errors.InitError,)


class MemoryKeyring(keyring.backend.KeyringBackend):
    """A keyring that stores credentials in a dictionary."""

    @properties.classproperty  #  type: ignore[misc]
    def priority(self) -> int | float:
        """Supply a priority.

        Indicating the priority of the backend relative to all other backends.
        """
        # Only > 0 make it to the chainer.
        return -1

    def __init__(self) -> None:
        super().__init__()

        self._credentials: dict[tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        """Set the service password for username in memory."""
        self._credentials[service, username] = password

    def get_password(self, service: str, username: str) -> str | None:
        """Get the service password for username from memory."""
        return self._credentials.get((service, username))

    def delete_password(self, service: str, username: str) -> None:
        """Delete the service password for username from memory."""
        try:
            del self._credentials[service, username]
        except KeyError as key_error:
            raise keyring.errors.PasswordDeleteError from key_error


class FileKeyring(keyring.backend.KeyringBackend):
    """A keyring that stores credentials in a file."""

    @properties.classproperty  #  type: ignore[misc]
    def priority(self) -> int | float:
        """Supply a priority.

        Indicating the priority of the backend relative to all other backends.
        """
        # Only > 0 make it to the chainer.
        return -1

    @property
    def credentials_file(self) -> Path:
        """Credentials file path for instance of application_name."""
        return (
            Path(BaseDirectory.save_data_path(self._application_name))
            / "credentials.json"
        )

    def _write_credentials(self) -> None:
        if not self.credentials_file.exists():
            self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            self.credentials_file.touch(mode=0o600)
        with self.credentials_file.open("w") as credentials_file:
            json.dump(self._credentials, credentials_file)

    def _read_credentials(self) -> None:
        try:
            with self.credentials_file.open() as credentials_file:
                self._credentials = json.load(credentials_file)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            self._credentials = {}

    def __init__(self, application_name: str) -> None:
        super().__init__()

        self._application_name = application_name
        self._read_credentials()

    def set_password(self, service: str, username: str, password: str) -> None:
        """Set the service password for username in memory."""
        if service not in self._credentials:
            self._credentials[service] = {username: password}
        else:
            self._credentials[service][username] = password
        self._write_credentials()

    def get_password(self, service: str, username: str) -> str | None:
        """Get the service password for username from memory."""
        try:
            return cast(str, self._credentials[service][username])
        except KeyError:
            return None

    def delete_password(self, service: str, username: str) -> None:
        """Delete the service password for username from memory."""
        try:
            del self._credentials[service][username]
        except KeyError as key_error:
            raise keyring.errors.PasswordDeleteError from key_error
        self._write_credentials()


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
        ephemeral: bool = False,
        environment_auth: str | None = None,
        *,
        file_fallback: bool = False,
    ) -> None:
        """Initialize Auth.

        :param application_name: name of the application using this library.
        :param host: specific host for the store used.
        :param environment_auth: environment variable used for authentication.
        :param ephemeral: keep everything in memory.
        :param file_fallback: fallback to FileKeyring if SecretService is not available.
        """
        self.application_name = application_name
        self.host = host

        environment_auth_value = None
        if environment_auth:
            environment_auth_value = os.getenv(environment_auth)

        if environment_auth_value or ephemeral:
            keyring.set_keyring(MemoryKeyring())

        self._keyring = keyring.get_keyring()
        # This keyring would fail on first use, fail early instead.
        # Only SecretService has get_preferred_collection, which can
        # fail if the keyring backend cannot be unlocked.
        if isinstance(self._keyring, SecretService.Keyring):
            try:
                self._keyring.get_preferred_collection()
            except keyring.errors.KeyringLocked as err:
                raise errors.KeyringUnlockError from err
            except KEYRING_EXCEPTIONS:
                self._fallback_to_file_keyring(application_name)
        elif isinstance(self._keyring, keyring.backends.fail.Keyring):
            if not file_fallback:
                raise errors.NoKeyringError
            self._fallback_to_file_keyring(application_name)

        if environment_auth_value:
            self.set_credentials(self.decode_credentials(environment_auth_value))

    def _fallback_to_file_keyring(self, application_name: str) -> None:
        logger.warning("Falling back to file based storage")
        keyring.set_keyring(FileKeyring(application_name))
        self._keyring = keyring.get_keyring()

    @staticmethod
    def decode_credentials(encoded_credentials: str) -> str:
        """Decode base64 encoded credentials.

        :raises errors.CredentialsNotParseable: when the credentials are incorrectly encoded.
        """
        try:
            return base64.b64decode(encoded_credentials).decode()
        except (binascii.Error, UnicodeDecodeError) as err:
            raise errors.CredentialsNotParseable from err

    @staticmethod
    def encode_credentials(credentials: str) -> str:
        """Encode credentials to base64."""
        return base64.b64encode(credentials.encode()).decode()

    def ensure_no_credentials(self) -> None:
        """Check that no credentials exist.

        :raises errors.CredentialsAvailable: if credentials have already been set.
        :raises errors.KeyringUnlockError: if the keyring cannot be unlocked.
        """
        try:
            password = self._keyring.get_password(self.application_name, self.host)
        except keyring.errors.KeyringLocked as exc:
            raise errors.KeyringUnlockError from exc

        if password is not None:
            raise errors.CredentialsAlreadyAvailable(self.application_name, self.host)

    def set_credentials(self, credentials: str, force: bool = False) -> None:
        """Store credentials in the keyring.

        :param credentials: token to store.
        :param force: overwrite existing credentials.
        """
        if not force:
            self.ensure_no_credentials()

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
            raise errors.CredentialsUnavailable(
                self.application_name, self.host
            ) from unknown_error

        if encoded_credentials_string is None:
            logger.debug("Credentials not found in the keyring %r", self._keyring.name)
            raise errors.CredentialsUnavailable(self.application_name, self.host)
        return self.decode_credentials(encoded_credentials_string)

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
