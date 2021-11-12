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

import keyring
import keyring.backend
import keyring.errors
import pytest

from craft_store import errors
from craft_store.auth import Auth, MemoryKeyring


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

    assert str(error.value) == ("Not logged in.")

    with pytest.raises(errors.NotLoggedIn) as error:
        auth.del_credentials()

    assert str(error.value) == ("Not logged in.")


def test_auth_from_environment(monkeypatch):
    monkeypatch.setenv("CREDENTIALS", "secret-keys")

    auth = Auth("fakecraft", "fakestore.com", "CREDENTIALS")

    assert auth.get_credentials() == "secret-keys"
