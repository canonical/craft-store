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

import logging
from typing import Any, List, Optional, Tuple
from unittest.mock import ANY, patch

import keyring
import keyring.backends.fail
import keyring.errors
import pytest

from craft_store import errors
from craft_store.auth import Auth, MemoryKeyring


class FakeKeyring:
    """Fake Keyring Backend implementation for tests."""

    name = "Fake Keyring"

    def __init__(self) -> None:
        self.set_password_calls: List[Tuple[Any, ...]] = []
        self.get_password_calls: List[Tuple[Any, ...]] = []
        self.delete_password_calls: List[Tuple[Any, ...]] = []
        self.password = None
        self.delete_error: Optional[Exception] = None

    def set_password(self, *args) -> None:
        """Set the service password for username in memory."""
        self.set_password_calls.append(args)
        self.password = args[2]

    def get_password(self, *args):
        """Get the service password for username from memory."""
        self.get_password_calls.append(args)
        return self.password

    def delete_password(self, *args):
        """Delete the service password for username from memory."""
        self.delete_password_calls.append(args)
        if self.delete_error is not None:
            # https://www.logilab.org/ticket/3207
            raise self.delete_error  # pylint: disable=raising-bad-type


@pytest.fixture
def keyring_set_keyring_mock():
    """Mock setting the keyring."""

    patched_keyring = patch("keyring.set_keyring", autospec=True)
    mocked_keyring = patched_keyring.start()
    yield mocked_keyring
    patched_keyring.stop()


@pytest.fixture
def fake_keyring():
    return FakeKeyring()


@pytest.fixture(autouse=True)
def fake_keyring_get(fake_keyring):
    """Mock keyring and return a FakeKeyring."""

    patched_keyring = patch("keyring.get_keyring")
    mocked_keyring = patched_keyring.start()
    mocked_keyring.return_value = fake_keyring
    yield mocked_keyring
    patched_keyring.stop()


def test_set_credentials(caplog, fake_keyring):
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_credentials("{'password': 'secret'}")

    assert fake_keyring.set_password_calls == [
        ("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="),
    ]
    assert caplog.records == []


def test_set_credentials_log_debug(caplog, fake_keyring):
    caplog.set_level(logging.DEBUG)
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_credentials("{'password': 'secret'}")

    assert fake_keyring.set_password_calls == [
        ("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="),
    ]
    assert [
        "Storing credentials for 'fakeclient' on 'fakestore.com' in keyring 'Fake Keyring'."
    ] == [rec.message for rec in caplog.records]


@pytest.mark.usefixtures("fake_keyring")
def test_double_set_credentials_fails():
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_credentials("{'password': 'secret'}")

    with pytest.raises(errors.CredentialsAvailable):
        auth.set_credentials("{'password': 'secret'}")


def test_get_credentials(caplog, fake_keyring):
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="

    auth = Auth("fakeclient", "fakestore.com")

    assert auth.get_credentials() == "{'password': 'secret'}"
    assert fake_keyring.get_password_calls == [("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_get_credentials_log_debug(caplog, fake_keyring):
    caplog.set_level(logging.DEBUG)
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="

    auth = Auth("fakeclient", "fakestore.com")

    assert auth.get_credentials() == "{'password': 'secret'}"
    assert fake_keyring.get_password_calls == [("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring 'Fake Keyring'."
    ] == [rec.message for rec in caplog.records]


def test_get_credentials_no_credentials_in_keyring(caplog, fake_keyring):
    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(errors.CredentialsUnavailable):
        auth.get_credentials()

    assert fake_keyring.get_password_calls == [("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_del_credentials(caplog, fake_keyring):
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="

    auth = Auth("fakeclient", "fakestore.com")

    auth.del_credentials()

    assert fake_keyring.delete_password_calls == [("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_del_credentials_log_debug(caplog, fake_keyring):
    caplog.set_level(logging.DEBUG)
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="

    auth = Auth("fakeclient", "fakestore.com")

    auth.del_credentials()

    assert fake_keyring.delete_password_calls == [("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring 'Fake Keyring'.",
        "Deleting credentials for 'fakeclient' on 'fakestore.com' from keyring 'Fake Keyring'.",
    ] == [rec.message for rec in caplog.records]


def test_del_credentials_delete_error_in_keyring(caplog, fake_keyring):
    fake_keyring.delete_error = keyring.errors.PasswordDeleteError()
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="

    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(keyring.errors.PasswordDeleteError):
        auth.del_credentials()

    assert fake_keyring.delete_password_calls == [("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_del_credentials_gets_no_credential(caplog, fake_keyring):
    caplog.set_level(logging.DEBUG)

    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(errors.CredentialsUnavailable):
        auth.del_credentials()

    assert fake_keyring.get_password_calls == [("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring 'Fake Keyring'.",
        "Credentials not found in the keyring 'Fake Keyring'",
    ] == [rec.message for rec in caplog.records]


def test_environment_set(monkeypatch, fake_keyring, keyring_set_keyring_mock):
    monkeypatch.setenv("FAKE_ENV", "c2VjcmV0LWtleXM=")

    Auth("fakeclient", "fakestore.com", environment_auth="FAKE_ENV")

    assert keyring_set_keyring_mock.mock_calls == [ANY]
    assert fake_keyring.set_password_calls == [
        ("fakeclient", "fakestore.com", "c2VjcmV0LWtleXM=")
    ]


def test_no_keyring_get(fake_keyring_get):
    fake_keyring_get.return_value = keyring.backends.fail.Keyring()

    with pytest.raises(errors.NoKeyringError):
        Auth("fakeclient", "fakestore.com")


def test_memory_keyring_set_get():
    k = MemoryKeyring()
    k.set_password("my-service", "my-user", "my-password")

    assert k.get_password("my-service", "my-user") == "my-password"


def test_memory_keyring_get_empty():
    k = MemoryKeyring()

    assert k.get_password("my-service", "my-user") is None


def test_memory_keyring_set_delete():
    k = MemoryKeyring()
    k.set_password("my-service", "my-user", "my-password")

    assert k.get_password("my-service", "my-user") == "my-password"

    k.delete_password("my-service", "my-user")

    assert k.get_password("my-service", "my-user") is None


def test_memory_keyring_delete_empty():
    k = MemoryKeyring()

    with pytest.raises(keyring.errors.PasswordDeleteError):
        k.delete_password("my-service", "my-user")
