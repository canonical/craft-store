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

from typing import Dict, Optional, Tuple

import keyring
import keyring.backend
import keyring.errors
import pytest

from craft_store import errors
from craft_store.auth import Auth


class MemoryKeyring(keyring.backend.KeyringBackend):
    """A test keyring that stores credentials in a dictionary."""

    priority = 1  # type: ignore

    def __init__(self) -> None:
        super().__init__()

        self._credentials: Dict[Tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        self._credentials[service, username] = password

    def get_password(self, service: str, username: str) -> Optional[str]:
        try:
            return self._credentials[service, username]
        except KeyError:
            return None

    def delete_password(self, service: str, username: str) -> None:
        try:
            del self._credentials[service, username]
        except KeyError as key_error:
            raise keyring.errors.PasswordDeleteError() from key_error


@pytest.fixture
def test_keyring():
    """In memory keyring backend for testing."""
    current_keyring = keyring.get_keyring()
    keyring.set_keyring(MemoryKeyring())
    yield
    keyring.set_keyring(current_keyring)


@pytest.mark.usefixtures("test_keyring")
def test_auth():
    auth = Auth("fakecraft", "fakestore.com")

    auth.set_credentials("foo")
    assert auth.get_credentials() == "foo"
    auth.del_credentials()

    with pytest.raises(errors.NotLoggedIn) as error:
        auth.get_credentials()

    assert str(error.value) == (
        "Not logged in: credentials not found in the keyring test auth MemoryKeyring."
    )

    with pytest.raises(errors.NotLoggedIn) as error:
        auth.del_credentials()

    assert str(error.value) == (
        "Not logged in: credentials not found in the keyring test auth MemoryKeyring."
    )
