#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
#  Copyright 2023 Canonical Ltd.
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
"""Tests for the store account model."""

import pytest
from craft_store.models.account_model import AccountModel

BASIC_ACCOUNT = {"id": "123"}
FULL_ACCOUNT = {
    "display-name": "Display Name",
    "email": "charmcrafters@lists.launchpad.net",
    "id": "abc123",
    "username": "usso-username",
    "validation": "unproven",
}


@pytest.mark.parametrize(
    ("json_dict", "expected"),
    [
        pytest.param(BASIC_ACCOUNT, AccountModel(id="123"), id="basic"),
        pytest.param(
            FULL_ACCOUNT,
            AccountModel(
                display_name="Display Name",  # pyright: ignore[reportCallIssue]
                # bug https://github.com/pydantic/pydantic/discussions/3986
                id="abc123",
                username="usso-username",
                validation="unproven",
                email="charmcrafters@lists.launchpad.net",
            ),
            id="fully-described",
        ),
    ],
)
def test_unmarshal(json_dict, expected):
    actual = AccountModel.unmarshal(json_dict)

    assert actual == expected


@pytest.mark.parametrize("payload", [BASIC_ACCOUNT, FULL_ACCOUNT])
def test_unmarshal_and_marshal(payload):
    assert AccountModel.unmarshal(payload).marshal() == payload
