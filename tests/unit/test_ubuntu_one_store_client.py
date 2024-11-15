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

import json
from unittest.mock import Mock, call, patch

import pytest
from craft_store import creds, endpoints, errors
from craft_store.ubuntu_one_store_client import UbuntuOneStoreClient
from pymacaroons import Caveat, Macaroon


def _fake_response(status_code, reason=None, headers=None, json=None):
    response = Mock(spec="requests.Response")
    response.status_code = status_code
    response.ok = status_code == 200
    response.headers = headers
    response.reason = reason
    if json is not None:
        response.json = Mock(return_value=json)
    return response


@pytest.fixture
def root_macaroon():
    return Macaroon(
        location="fake-server.com",
        signature="d9533461d7835e4851c7e3b639144406cf768597dea6e133232fbd2385a5c050",
        caveats=[
            Caveat(
                caveat_id="1234567890",
                location="fake-sso.com",
                verification_key_id="1234567890",
            )
        ],
    ).serialize()


@pytest.fixture
def discharged_macaroon():
    return Macaroon(
        location="fake-server.com",
        signature="d9533461d7835e4851c7e3b639122406cf768597dea6e133232fbd2385a5c050",
    ).serialize()


@pytest.fixture
def u1_macaroon_value(root_macaroon, discharged_macaroon):
    """The basic "payload" for the u1-macaroon auth type"""
    return {"r": root_macaroon, "d": discharged_macaroon}


@pytest.fixture
def old_credentials(u1_macaroon_value):
    """u1-macaroon credentials encoded in the *old* ("type-less") scheme."""
    return json.dumps(u1_macaroon_value)


@pytest.fixture
def new_credentials(u1_macaroon_value):
    """u1-macaroon credentials encoded in the *new* ("typed") scheme."""
    return creds.marshal_u1_credentials(creds.UbuntuOneMacaroons(**u1_macaroon_value))


@pytest.fixture
def authorization():
    return (
        "Macaroon "
        "root=MDAxZGxvY2F0aW9uIGZha2Utc2VydmVyLmNvbQowMDEwaWRlbnRpZmllciAKMDAxM2NpZCAxMjM0NTY3ODkwCjAwMTN2aWQgMTIzNDU2Nzg5MAowMDE0Y2wgZmFrZS1zc28uY29tCjAwMmZzaWduYXR1cmUg2VM0YdeDXkhRx-O2ORREBs92hZfepuEzIy-9I4WlwFAK, "
        "discharge=MDAxZGxvY2F0aW9uIGZha2Utc2VydmVyLmNvbQowMDEwaWRlbnRpZmllciAKMDAyZnNpZ25hdHVyZSB6hf06Su8kgum0keaUXy6VxGUHlN9bFL2A0EKNptFZMwo"
    )


@pytest.fixture
def http_client_request_mock(root_macaroon, discharged_macaroon):
    def request(*args, **kwargs):
        if args[1] == "POST" and "tokens/discharge" in args[2]:
            email = kwargs["json"]["email"]
            otp = kwargs["json"].get("otp")
            if email == "otp@foo.bar" and otp is None:
                response = _fake_response(
                    401,
                    json={
                        "error_list": [
                            {"code": "twofactor-required", "message": "otp required"}
                        ]
                    },
                )
            else:
                response = _fake_response(
                    200,
                    json={"discharge_macaroon": discharged_macaroon},
                )
        elif args[1] == "POST" and "/tokens/refresh" in args[2]:
            response = _fake_response(
                200,
                json={"discharge_macaroon": discharged_macaroon},
            )
        elif args[1] == "POST" and "/dev/api/acl/" in args[2]:
            response = _fake_response(200, json={"macaroon": root_macaroon})
        elif args[1] == "GET" and "whoami" in args[2]:
            response = _fake_response(
                200,
                json={"name": "Fake Person", "username": "fakeuser", "id": "fake-id"},
            )
        else:
            response = _fake_response(200)

        return response

    patched_http_client = patch(
        "craft_store.base_client.HTTPClient.request",
        autospec=True,
        side_effect=request,
    )
    mocked_http_client = patched_http_client.start()
    yield mocked_http_client
    patched_http_client.stop()


@pytest.fixture
def auth_mock(old_credentials, new_credentials, new_auth):
    patched_auth = patch("craft_store.base_client.Auth", autospec=True)
    mocked_auth = patched_auth.start()

    credentials = new_credentials if new_auth else old_credentials

    mocked_auth.return_value.get_credentials.return_value = credentials
    # Note that the call to encode credentials always encode the new format.
    mocked_auth.return_value.encode_credentials.return_value = new_credentials
    yield mocked_auth
    patched_auth.stop()


@pytest.mark.parametrize("environment_auth", [None, "APPLICATION_CREDENTIALS"])
def test_store_client_login(
    http_client_request_mock,
    new_credentials,
    auth_mock,
    environment_auth,
    expires,
):
    store_client = UbuntuOneStoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        auth_url="https://fake-sso.com",
        endpoints=endpoints.U1_SNAP_STORE,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
        environment_auth=environment_auth,
    )

    assert (
        store_client.login(
            permissions=["perm-1", "perm-2"],
            description="fakecraft@foo",
            ttl=60,
            email="foo@bar.com",
            password="password",  # noqa: S106
        )
        == new_credentials
    )

    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "POST",
            "https://fake-server.com/dev/api/acl/",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "permissions": ["perm-1", "perm-2"],
                "description": "fakecraft@foo",
                "expires": expires(60),
            },
        ),
        call(
            store_client.http_client,
            "POST",
            "https://fake-sso.com/api/v2/tokens/discharge",
            json={
                "email": "foo@bar.com",
                "password": "password",
                "caveat_id": "1234567890",
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        ),
    ]

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=environment_auth,
            ephemeral=False,
            file_fallback=False,
        ),
        call().ensure_no_credentials(),
        call().set_credentials(new_credentials),
        call().encode_credentials(new_credentials),
    ]


def test_store_client_login_otp(
    http_client_request_mock,
    new_credentials,
    auth_mock,
    expires,
):
    store_client = UbuntuOneStoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        auth_url="https://fake-sso.com",
        endpoints=endpoints.U1_SNAP_STORE,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    with pytest.raises(errors.StoreServerError) as server_error:
        store_client.login(
            permissions=["perm-1", "perm-2"],
            description="fakecraft@foo",
            ttl=60,
            email="otp@foo.bar",
            password="password",  # noqa: S106
        )
    assert "twofactor-required" in server_error.value.error_list

    assert (
        store_client.login(
            permissions=["perm-1", "perm-2"],
            description="fakecraft@foo",
            ttl=60,
            email="otp@foo.bar",
            password="password",  # noqa: S106
            otp="123456",
        )
        == new_credentials
    )

    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "POST",
            "https://fake-server.com/dev/api/acl/",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "permissions": ["perm-1", "perm-2"],
                "description": "fakecraft@foo",
                "expires": expires(60),
            },
        ),
        call(
            store_client.http_client,
            "POST",
            "https://fake-sso.com/api/v2/tokens/discharge",
            json={
                "email": "otp@foo.bar",
                "password": "password",
                "caveat_id": "1234567890",
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        ),
        call(
            store_client.http_client,
            "POST",
            "https://fake-server.com/dev/api/acl/",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "permissions": ["perm-1", "perm-2"],
                "description": "fakecraft@foo",
                "expires": expires(60),
            },
        ),
        call(
            store_client.http_client,
            "POST",
            "https://fake-sso.com/api/v2/tokens/discharge",
            json={
                "email": "otp@foo.bar",
                "password": "password",
                "otp": "123456",
                "caveat_id": "1234567890",
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        ),
    ]

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=None,
            ephemeral=False,
            file_fallback=False,
        ),
        # First call without otp.
        call().ensure_no_credentials(),
        # Second call with otp.
        call().ensure_no_credentials(),
        call().set_credentials(new_credentials),
        call().encode_credentials(new_credentials),
    ]


def test_store_client_login_with_packages_and_channels(
    http_client_request_mock, new_credentials, auth_mock, expires
):
    store_client = UbuntuOneStoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        auth_url="https://fake-sso.com",
        endpoints=endpoints.U1_SNAP_STORE,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    assert (
        store_client.login(
            permissions=["perm-1", "perm-2"],
            description="fakecraft@foo",
            ttl=60,
            channels=["edge"],
            packages=[
                endpoints.Package("my-snap", "snap"),
                endpoints.Package("my-other-snap", "snap"),
            ],
            email="foo@bar.com",
            password="password",  # noqa: S106
        )
        == new_credentials
    )

    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "POST",
            "https://fake-server.com/dev/api/acl/",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "permissions": ["perm-1", "perm-2"],
                "description": "fakecraft@foo",
                "expires": expires(60),
                "packages": [
                    {
                        "name": "my-snap",
                        "series": "16",
                    },
                    {
                        "name": "my-other-snap",
                        "series": "16",
                    },
                ],
                "channels": ["edge"],
            },
        ),
        call(
            store_client.http_client,
            "POST",
            "https://fake-sso.com/api/v2/tokens/discharge",
            json={
                "email": "foo@bar.com",
                "password": "password",
                "caveat_id": "1234567890",
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        ),
    ]

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=None,
            ephemeral=False,
            file_fallback=False,
        ),
        call().ensure_no_credentials(),
        call().set_credentials(new_credentials),
        call().encode_credentials(new_credentials),
    ]


def test_store_client_logout(auth_mock):
    store_client = UbuntuOneStoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        auth_url="https://fake-sso.com",
        endpoints=endpoints.U1_SNAP_STORE,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    store_client.logout()

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=None,
            ephemeral=False,
            file_fallback=False,
        ),
        call().del_credentials(),
    ]


def test_store_client_request(http_client_request_mock, authorization, auth_mock):
    store_client = UbuntuOneStoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        auth_url="https://fake-sso.com",
        endpoints=endpoints.U1_SNAP_STORE,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    store_client.request("GET", "https://fake-server.com/fakepath")

    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "GET",
            "https://fake-server.com/fakepath",
            params=None,
            headers={"Authorization": authorization},
        )
    ]

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=None,
            ephemeral=False,
            file_fallback=False,
        ),
        call().get_credentials(),
    ]


def test_store_client_request_refresh(
    http_client_request_mock,
    new_credentials,
    authorization,
    discharged_macaroon,
    auth_mock,
):
    http_client_request_mock.side_effect = [
        errors.StoreServerError(
            _fake_response(
                401,
                json={
                    "error_list": [
                        {
                            "code": "macaroon-needs-refresh",
                            "message": "Expired macaroon (age: 1234567 seconds)",
                        }
                    ]
                },
            )
        ),
        _fake_response(200, json={"discharge_macaroon": discharged_macaroon}),
        _fake_response(200),
    ]
    store_client = UbuntuOneStoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        auth_url="https://fake-sso.com",
        endpoints=endpoints.U1_SNAP_STORE,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    store_client.request("GET", "https://fake-server.com/refreshpath")

    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "GET",
            "https://fake-server.com/refreshpath",
            params=None,
            headers={"Authorization": authorization},
        ),
        call(
            store_client.http_client,
            "POST",
            "https://fake-sso.com/api/v2/tokens/refresh",
            json={"discharge_macaroon": discharged_macaroon},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        ),
        call(
            store_client.http_client,
            "GET",
            "https://fake-server.com/refreshpath",
            params=None,
            headers={"Authorization": authorization},
        ),
    ]

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=None,
            ephemeral=False,
            file_fallback=False,
        ),
        call().get_credentials(),
        call().get_credentials(),
        call().set_credentials(new_credentials, force=True),
        call().get_credentials(),
    ]


def test_store_client_whoami(http_client_request_mock, authorization, auth_mock):
    store_client = UbuntuOneStoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        auth_url="https://fake-sso.com",
        endpoints=endpoints.U1_SNAP_STORE,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    assert store_client.whoami() == {
        "name": "Fake Person",
        "username": "fakeuser",
        "id": "fake-id",
    }

    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "GET",
            "https://fake-server.com/api/v2/tokens/whoami",
            params=None,
            headers={
                "Authorization": authorization,
            },
        )
    ]

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=None,
            ephemeral=False,
            file_fallback=False,
        ),
        call().get_credentials(),
    ]
