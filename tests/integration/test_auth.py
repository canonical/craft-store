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
from jaraco.classes import properties

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


class _BrokenInitKeyring(keyring.backend.KeyringBackend):
    """Keyring that raises InitError on all operations.

    Simulates a SecretService keyring on a headless machine where the
    collection cannot be created or accessed (e.g. "Prompt dismissed.").
    """

    @properties.classproperty  # type: ignore[misc]
    def priority(self) -> int | float:
        return 1

    def set_password(self, service: str, username: str, password: str) -> None:
        raise keyring.errors.InitError(
            "Failed to create the collection: Prompt dismissed."
        )

    def get_password(self, service: str, username: str) -> str | None:
        raise keyring.errors.InitError(
            "Failed to create the collection: Prompt dismissed."
        )

    def delete_password(self, service: str, username: str) -> None:
        raise keyring.errors.InitError(
            "Failed to create the collection: Prompt dismissed."
        )


@pytest.fixture
def _broken_init_keyring():
    current_keyring = keyring.get_keyring()
    keyring.set_keyring(_BrokenInitKeyring())
    yield
    keyring.set_keyring(current_keyring)


@pytest.mark.usefixtures("_broken_init_keyring")
def test_auth_ensure_no_credentials_headless_keyring():
    """Regression test for https://github.com/canonical/craft-store/issues/58.

    On a headless machine, keyring operations raise InitError because the
    SecretService collection cannot be unlocked interactively. This must
    surface as a KeyringUnlockError rather than an unhandled internal error.
    """
    auth = Auth("fakecraft", "fakestore.com")

    with pytest.raises(errors.KeyringUnlockError):
        auth.ensure_no_credentials()
