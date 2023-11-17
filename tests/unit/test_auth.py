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
import sys
from typing import List, Type
from unittest.mock import ANY

import keyring
import keyring.backends.fail
import keyring.errors
import pytest
from craft_store import errors
from craft_store.auth import Auth, FileKeyring, MemoryKeyring
from keyring.backends import SecretService


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

    with pytest.raises(errors.CredentialsAlreadyAvailable):
        auth.set_credentials("{'password': 'secret'}")


def test_double_set_credentials_force(fake_keyring):
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_credentials("{'password': 'secret'}")

    auth.set_credentials("{'password': 'secret2'}", force=True)

    assert fake_keyring.set_password_calls == [
        ("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="),
        ("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQyJ30="),
    ]


def test_get_credentials(caplog, fake_keyring):
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="  # noqa: S105

    auth = Auth("fakeclient", "fakestore.com")

    assert auth.get_credentials() == "{'password': 'secret'}"
    assert fake_keyring.get_password_calls == [("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_get_credentials_log_debug(caplog, fake_keyring):
    caplog.set_level(logging.DEBUG)
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="  # noqa: S105

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
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="  # noqa: S105

    auth = Auth("fakeclient", "fakestore.com")

    auth.del_credentials()

    assert fake_keyring.delete_password_calls == [("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_del_credentials_log_debug(caplog, fake_keyring):
    caplog.set_level(logging.DEBUG)
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="  # noqa: S105

    auth = Auth("fakeclient", "fakestore.com")

    auth.del_credentials()

    assert fake_keyring.delete_password_calls == [("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring 'Fake Keyring'.",
        "Deleting credentials for 'fakeclient' on 'fakestore.com' from keyring 'Fake Keyring'.",
    ] == [rec.message for rec in caplog.records]


def test_del_credentials_delete_error_in_keyring(caplog, fake_keyring):
    fake_keyring.delete_error = keyring.errors.PasswordDeleteError()
    fake_keyring.password = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="  # noqa: S105

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


def test_credentials_not_parseable_error(monkeypatch):
    monkeypatch.setenv("FAKE_ENV", "12345")

    with pytest.raises(errors.CredentialsNotParseable):
        Auth("fakeclient", "fakestore.com", environment_auth="FAKE_ENV")


def test_environment_set(monkeypatch, fake_keyring, keyring_set_keyring_mock):
    monkeypatch.setenv("FAKE_ENV", "c2VjcmV0LWtleXM=")

    Auth("fakeclient", "fakestore.com", environment_auth="FAKE_ENV")

    assert keyring_set_keyring_mock.mock_calls == [ANY]
    assert fake_keyring.set_password_calls == [
        ("fakeclient", "fakestore.com", "c2VjcmV0LWtleXM=")
    ]


def test_ensure_no_credentials_unlock_error(fake_keyring, mocker):
    mocker.patch.object(
        fake_keyring, "get_password", side_effect=errors.KeyringUnlockError
    )

    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(errors.KeyringUnlockError):
        auth.ensure_no_credentials()


@pytest.mark.disable_fake_keyring()
def test_ephemeral_set_memory_keyring():
    auth = Auth("fakeclient", "fakestore.com", ephemeral=True)

    assert isinstance(auth._keyring, MemoryKeyring)  # pylint: disable=protected-access


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


@pytest.fixture(autouse=True)
def _fake_basedirectory(mocker, tmp_path):
    mocker.patch("craft_store.auth.BaseDirectory.save_data_path", return_value=tmp_path)


def test_file_keyring_set_get():
    k = FileKeyring("test-app")
    k.set_password("my-service", "my-user", "my-password")

    assert k.get_password("my-service", "my-user") == "my-password"


def test_file_keyring_get_empty():
    k = FileKeyring("test-app")

    assert k.get_password("my-service", "my-user") is None


def test_file_keyring_set_delete():
    k = FileKeyring("test-app")
    k.set_password("my-service", "my-user", "my-password")

    assert k.get_password("my-service", "my-user") == "my-password"

    k.delete_password("my-service", "my-user")

    assert k.get_password("my-service", "my-user") is None


def test_file_keyring_delete_empty():
    k = FileKeyring("test-app")

    with pytest.raises(keyring.errors.PasswordDeleteError):
        k.delete_password("my-service", "my-user")


def test_file_keyring_storage_path(tmp_path):
    """Ensure the mock is used."""
    k = FileKeyring("test-app")

    assert k.credentials_file == tmp_path / "credentials.json"


test_exceptions: List[Type[Exception]] = [keyring.errors.InitError]
if sys.platform == "linux":
    from secretstorage.exceptions import SecretServiceNotAvailableException

    test_exceptions.append(SecretServiceNotAvailableException)


@pytest.mark.disable_fake_keyring()
@pytest.mark.parametrize("exception", test_exceptions)
def test_secretservice_file_fallsback(mocker, exception):
    # At one point in the code we run keyring.set_backend, there is no
    # elegant way to reset this in the library.
    keyring.set_keyring(SecretService.Keyring())
    mocker.patch(
        "keyring.backends.SecretService.Keyring.get_preferred_collection",
        side_effect=exception,
    )
    auth = Auth(application_name="test-app", host="foo")

    assert type(auth._keyring) == FileKeyring


@pytest.mark.disable_fake_keyring()
def test_secretservice_works(mocker):
    # At one point in the code we run keyring.set_backend, there is no
    # elegant way to reset this in the library.
    keyring.set_keyring(SecretService.Keyring())
    mocker.patch(
        "keyring.backends.SecretService.Keyring.get_preferred_collection",
        return_value=None,
    )
    auth = Auth(application_name="test-app", host="foo")

    assert type(auth._keyring) == SecretService.Keyring
