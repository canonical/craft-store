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
from collections import namedtuple
from unittest.mock import ANY, call, patch

import keyring.errors
import pytest

from craft_store import errors
from craft_store.auth import Auth, MemoryKeyring


@pytest.fixture(autouse=True)
def keyring_get_keyring_mock():
    """Mock getting the keyring."""

    patched_keyring = patch("keyring.get_keyring", autospec=True)
    mocked_keyring = patched_keyring.start()
    mocked_keyring.return_value = namedtuple("FakeKeyring", ["name"])("Fake Keyring")
    yield mocked_keyring
    patched_keyring.stop()


@pytest.fixture(autouse=True)
def keyring_set_keyring_mock():
    """Mock setting the keyring."""

    patched_keyring = patch("keyring.set_keyring", autospec=True)
    mocked_keyring = patched_keyring.start()
    yield mocked_keyring
    patched_keyring.stop()


@pytest.fixture
def keyring_set_mock():
    """Mock for keyring.set_password."""
    patched_keyring = patch("keyring.set_password", autospec=True)
    mocked_keyring = patched_keyring.start()
    yield mocked_keyring
    patched_keyring.stop()


@pytest.fixture
def keyring_get_mock():
    """Mock for keyring.get_password."""
    patched_keyring = patch(
        "keyring.get_password",
        autospec=True,
        return_value="eydwYXNzd29yZCc6ICdzZWNyZXQnfQ==",
    )
    mocked_keyring = patched_keyring.start()
    yield mocked_keyring
    patched_keyring.stop()


@pytest.fixture
def keyring_delete_mock():
    """Mock for keyring.get_password."""
    patched_keyring = patch("keyring.delete_password", autospec=True, return_value=None)
    mocked_keyring = patched_keyring.start()
    yield mocked_keyring
    patched_keyring.stop()


def test_set_credentials(caplog, keyring_set_mock):
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_credentials("{'password': 'secret'}")

    assert keyring_set_mock.mock_calls == [
        call("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ==")
    ]
    assert caplog.records == []


def test_set_credentials_log_debug(caplog, keyring_set_mock):
    caplog.set_level(logging.DEBUG)
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_credentials("{'password': 'secret'}")

    assert keyring_set_mock.mock_calls == [
        call("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ==")
    ]
    assert ["Storing credentials for 'fakeclient' on 'fakestore.com' in keyring."] == [
        rec.message for rec in caplog.records
    ]


def test_get_credentials(caplog, keyring_get_mock):
    auth = Auth("fakeclient", "fakestore.com")

    assert auth.get_credentials() == "{'password': 'secret'}"
    assert keyring_get_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_get_credentials_log_debug(caplog, keyring_get_mock):
    caplog.set_level(logging.DEBUG)

    auth = Auth("fakeclient", "fakestore.com")

    assert auth.get_credentials() == "{'password': 'secret'}"
    assert keyring_get_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring."
    ] == [rec.message for rec in caplog.records]


def test_get_credentials_no_credentials_in_keyring(caplog, keyring_get_mock):
    keyring_get_mock.return_value = None

    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(errors.NotLoggedIn):
        auth.get_credentials()

    assert keyring_get_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []


@pytest.mark.usefixtures("keyring_get_mock")
def test_del_credentials(caplog, keyring_delete_mock):
    auth = Auth("fakeclient", "fakestore.com")

    auth.del_credentials()

    assert keyring_delete_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []


@pytest.mark.usefixtures("keyring_get_mock")
def test_del_credentials_log_debug(caplog, keyring_delete_mock):
    caplog.set_level(logging.DEBUG)

    auth = Auth("fakeclient", "fakestore.com")

    auth.del_credentials()

    assert keyring_delete_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring.",
        "Deleting credentials for 'fakeclient' on 'fakestore.com' from keyring: 'Fake Keyring'.",
    ] == [rec.message for rec in caplog.records]


@pytest.mark.usefixtures("keyring_get_mock")
def test_del_credentials_delete_error_in_keyring(caplog, keyring_delete_mock):
    keyring_delete_mock.side_effect = keyring.errors.PasswordDeleteError()

    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(keyring.errors.PasswordDeleteError):
        auth.del_credentials()

    assert keyring_delete_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_del_credentials_gets_no_credential(caplog, keyring_get_mock):
    caplog.set_level(logging.DEBUG)
    keyring_get_mock.return_value = None

    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(errors.NotLoggedIn):
        auth.del_credentials()

    assert keyring_get_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring.",
        "Credentials not found in the keyring 'Fake Keyring'",
    ] == [rec.message for rec in caplog.records]


def test_environment_set(monkeypatch, keyring_set_keyring_mock, keyring_set_mock):
    monkeypatch.setenv("FAKE_ENV", "keys-to-the-kingdom")

    Auth("fakeclient", "fakestore.com", environment_auth="FAKE_ENV")

    assert keyring_set_keyring_mock.mock_calls == [ANY]
    assert keyring_set_mock.mock_calls == [
        call("fakeclient", "fakestore.com", "a2V5cy10by10aGUta2luZ2RvbQ==")
    ]


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
