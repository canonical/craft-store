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
from unittest.mock import call, patch

import keyring.errors
import pytest

from craft_store import errors
from craft_store.auth import Auth


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
    patched_keyring = patch("keyring.get_password", autospec=True, return_value=None)
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


def test_set_auth(caplog, keyring_set_mock):
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_auth("{'password': 'secret'}")

    assert keyring_set_mock.mock_calls == [
        call("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ==")
    ]
    assert caplog.records == []


def test_set_auth_log_debug(caplog, keyring_set_mock):
    caplog.set_level(logging.DEBUG)
    auth = Auth("fakeclient", "fakestore.com")

    auth.set_auth("{'password': 'secret'}")

    assert keyring_set_mock.mock_calls == [
        call("fakeclient", "fakestore.com", "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ==")
    ]
    assert ["Storing credentials for 'fakeclient' on 'fakestore.com' in keyring."] == [
        rec.message for rec in caplog.records
    ]


def test_get_auth(caplog, keyring_get_mock):
    keyring_get_mock.return_value = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="

    auth = Auth("fakeclient", "fakestore.com")

    assert auth.get_auth() == "{'password': 'secret'}"
    assert keyring_get_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_get_auth_log_debug(caplog, keyring_get_mock):
    caplog.set_level(logging.DEBUG)
    keyring_get_mock.return_value = "eydwYXNzd29yZCc6ICdzZWNyZXQnfQ=="

    auth = Auth("fakeclient", "fakestore.com")

    assert auth.get_auth() == "{'password': 'secret'}"
    assert keyring_get_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert [
        "Retrieving credentials for 'fakeclient' on 'fakestore.com' from keyring."
    ] == [rec.message for rec in caplog.records]


def test_get_auth_no_auth_in_keyring(caplog, keyring_get_mock):
    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(errors.NotLoggedIn):
        auth.get_auth()

    assert keyring_get_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_del_auth(caplog, keyring_delete_mock):
    auth = Auth("fakeclient", "fakestore.com")

    auth.del_auth()

    assert keyring_delete_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []


def test_del_auth_log_debug(caplog, keyring_delete_mock):
    caplog.set_level(logging.DEBUG)

    auth = Auth("fakeclient", "fakestore.com")

    auth.del_auth()

    assert keyring_delete_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert [
        "Deleting credentials for 'fakeclient' on 'fakestore.com' from keyring."
    ] == [rec.message for rec in caplog.records]


def test_del_auth_no_auth_in_keyring(caplog, keyring_delete_mock):
    keyring_delete_mock.side_effect = keyring.errors.PasswordDeleteError()

    auth = Auth("fakeclient", "fakestore.com")

    with pytest.raises(errors.NotLoggedIn):
        auth.del_auth()

    assert keyring_delete_mock.mock_calls == [call("fakeclient", "fakestore.com")]
    assert caplog.records == []
