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

pytestmark = pytest.mark.timeout(10)  # Timeout if any test takes over 10 sec.


@pytest.fixture
def _test_keyring():
    """In memory keyring backend for testing."""
    current_keyring = keyring.get_keyring()
    keyring.set_keyring(MemoryKeyring())
    yield
    keyring.set_keyring(current_keyring)


@pytest.mark.usefixtures("_test_keyring")
def test_auth():
    auth = Auth("fakecraft", "fakestore.com")

    auth.set_credentials("foo")
    assert auth.get_credentials() == "foo"
    auth.del_credentials()

    with pytest.raises(errors.CredentialsUnavailable) as error:
        auth.get_credentials()

    assert str(error.value) == (
        "No credentials found for 'fakecraft' on 'fakestore.com'."
    )

    with pytest.raises(errors.CredentialsUnavailable) as error:
        auth.del_credentials()

    assert str(error.value) == (
        "No credentials found for 'fakecraft' on 'fakestore.com'."
    )


def test_auth_from_environment(monkeypatch):
    monkeypatch.setenv("CREDENTIALS", "c2VjcmV0LWtleXM=")

    auth = Auth("fakecraft", "fakestore.com", environment_auth="CREDENTIALS")

    assert auth.get_credentials() == "secret-keys"
