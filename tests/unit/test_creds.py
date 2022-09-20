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


def test_u1_creds_unmarshal_failure():
    with pytest.raises(errors.CredentialsNotParseable):
        creds.unmarshal_u1_credentials("not a valid json string")
