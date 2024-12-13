# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022,2024 Canonical Ltd.
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

import datetime
from typing import Any
from unittest import mock
from unittest.mock import patch

import craft_store
import pytest
from craft_store.publisher import RegisteredName


class FakeKeyring:
    """Fake Keyring Backend implementation for tests."""

    name = "Fake Keyring"

    def __init__(self) -> None:
        self.set_password_calls: list[tuple[Any, ...]] = []
        self.get_password_calls: list[tuple[Any, ...]] = []
        self.delete_password_calls: list[tuple[Any, ...]] = []
        self.password = None
        self.delete_error: Exception | None = None

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
            raise self.delete_error


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
def fake_keyring_get(fake_keyring, request):
    """Mock keyring and return a FakeKeyring."""
    if "disable_fake_keyring" in request.keywords:
        yield
    else:
        patched_keyring = patch("keyring.get_keyring")
        mocked_keyring = patched_keyring.start()
        mocked_keyring.return_value = fake_keyring
        yield mocked_keyring
        patched_keyring.stop()


@pytest.fixture
def expires():
    """Mocks/freezes utcnow() in craft_store.endpoints module.

    Provides a function for creating expected iso formatted expires datetime
    values.
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    def offset_iso_dt(seconds=0):
        return (
            (now + datetime.timedelta(seconds=seconds))
            .replace(microsecond=0)
            .isoformat()
        )

    with patch("craft_store.endpoints.datetime", wraps=datetime.datetime) as dt_mock:
        dt_mock.utcnow.return_value = now
        yield offset_iso_dt


@pytest.fixture(params=[True, False], ids=["new_auth", "old_auth"])
def new_auth(request) -> bool:
    """
    Parametrized fixture representing either the new, type-based auth storage (True) or the old one (False).

    :see: base_client.wrap_credentials()
    """
    return request.param


@pytest.fixture
def mock_auth():
    return mock.Mock(spec=craft_store.Auth)


@pytest.fixture
def fake_registered_name_dict():
    return {
        "id": "0",
        "name": "my-package",
        "private": False,
        "publisher": {"id": "0"},
        "status": "tired",
        "store": "charmhub",
        "type": "charm",
    }


@pytest.fixture
def fake_registered_name_model(fake_registered_name_dict):
    return RegisteredName.unmarshal(fake_registered_name_dict)
