# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
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

import json

import pytest
from craft_store import creds, errors


@pytest.fixture
def stored_candid_creds(new_auth: bool) -> str:
    """Fixture that generates Candid credentials in the format read from storage.

    The credentials will either be a raw string (if `new_auth` is False) or a JSON'ed
    dict encoding the credentials type (if `new_auth` is True).
    """
    candid_creds = "fake candid creds"
    if new_auth:
        return json.dumps({"t": "macaroon", "v": candid_creds})

    return candid_creds


@pytest.fixture
def stored_u1_creds(new_auth: bool) -> str:
    """Fixture that generates Ubuntu One credentials in the format read from storage.

    The stored credentials are always a JSON'ed dict. The dict itself is either in the
    "old" format listing the root and discharge macaroons (if `new_auth` is False) or
    in the "new" format listing the credentials type *and* the macaroons (if `new_auth`
    is True).
    """
    u1_creds = {"r": "fake root macaroon", "d": "fake discharge macaroon"}
    if new_auth:
        return json.dumps({"t": "u1-macaroon", "v": u1_creds})
    return json.dumps(u1_creds)


@pytest.fixture
def stored_developer_token() -> str:
    """Fixture that generates developer token in the format read from storage."""
    dev_token = {"macaroon": "test-dev-token"}
    return json.dumps(dev_token)


def test_candid_creds_unmarshal(stored_candid_creds):
    """Test that we can parse both types of stored Candid creds."""
    candid_creds = creds.unmarshal_candid_credentials(stored_candid_creds)
    assert candid_creds == "fake candid creds"


def test_candid_creds_marshal():
    marshalled = creds.marshal_candid_credentials("fake candid creds")
    loaded = json.loads(marshalled)

    assert len(loaded) == 2
    assert loaded["t"] == "macaroon"
    assert loaded["v"] == "fake candid creds"


def test_u1_creds_unmarshal(stored_u1_creds):
    """Test that we can parse both types of stored Ubuntu One creds."""
    u1_creds = creds.unmarshal_u1_credentials(stored_u1_creds)
    assert u1_creds.root == "fake root macaroon"
    assert u1_creds.discharge == "fake discharge macaroon"


def test_u1_creds_marshal():
    macaroons = creds.UbuntuOneMacaroons(r="fake root", d="fake discharge")
    marshalled = creds.marshal_u1_credentials(macaroons)
    loaded = json.loads(marshalled)

    assert len(loaded) == 2
    assert loaded["t"] == "u1-macaroon"
    assert len(loaded["v"]) == 2
    assert loaded["v"]["r"] == "fake root"
    assert loaded["v"]["d"] == "fake discharge"


def test_u1_creds_with_discharge():
    """Return new credentials with an updated discharge macaroon."""
    original_creds = creds.UbuntuOneMacaroons(r="original root", d="original discharge")

    new_creds = original_creds.with_discharge("new discharge")

    assert original_creds.root == "original root"
    assert original_creds.discharge == "original discharge"
    assert new_creds.root == "original root"
    assert new_creds.discharge == "new discharge"


def test_u1_creds_unmarshal_failure():
    with pytest.raises(errors.CredentialsNotParseable):
        creds.unmarshal_u1_credentials("not a valid json string")


def test_mixed_creds():
    """Test the case of trying to load the wrong type of credentials."""
    macaroons = creds.UbuntuOneMacaroons(r="fake root", d="fake discharge")
    stored_u1 = creds.marshal_u1_credentials(macaroons)

    stored_candid = creds.marshal_candid_credentials("fake candid")

    # Try to load Ubuntu One as Candid:
    with pytest.raises(errors.CredentialsNotParseable):
        creds.unmarshal_candid_credentials(stored_u1)

    # Try to load Candid as Ubuntu One:
    with pytest.raises(errors.CredentialsNotParseable):
        creds.unmarshal_u1_credentials(stored_candid)


def test_developer_token_marshal():
    dev_token = creds.DeveloperToken(macaroon="test-cred")
    json_dev_token = dev_token.model_dump_json()
    loaded = json.loads(json_dev_token)
    assert len(loaded) == 1, "Dict with single key should be stored"
    assert loaded["macaroon"] == dev_token.macaroon, (
        "Serialized and deserialized object should be the same as base one"
    )


def test_developer_token_unmarshal(stored_developer_token: str):
    developer_token = creds.DeveloperToken.model_validate_json(stored_developer_token)
    assert developer_token.macaroon == "test-dev-token"


def test_developer_token_loading_failure():
    with pytest.raises(errors.CredentialsNotParseable):
        creds.DeveloperToken.model_validate_json("incorrect-creds")


def test_developer_token_incorrect_type():
    with pytest.raises(errors.CredentialsNotParseable):
        creds.DeveloperToken.unmarshal({"incorrect-creds": "some"})
