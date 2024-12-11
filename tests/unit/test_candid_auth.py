#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*
#
#  Copyright 2024 Canonical Ltd.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License version 3 as published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""Tests for authorizing requests using CandidAuth."""


import httpx
import pytest
from craft_store import CandidAuth


@pytest.fixture
def candid_auth(mock_auth):
    return CandidAuth(
        auth=mock_auth,
    )


def test_get_token_from_keyring(mock_auth, candid_auth):
    mock_auth.get_credentials.return_value = "{}"

    assert candid_auth.get_token_from_keyring() == "{}"


def test_auth_flow(mock_auth, candid_auth):
    mock_auth.get_credentials.return_value = "{}"

    request = httpx.Request("GET", "http://localhost")

    next(candid_auth.auth_flow(request))

    assert request.headers["Authorization"] == "Bearer {}"
