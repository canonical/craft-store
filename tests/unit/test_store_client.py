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
from unittest.mock import ANY, Mock, call, patch

import pytest
from macaroonbakery import bakery, httpbakery
from pymacaroons.macaroon import Macaroon

from craft_store import endpoints, errors
from craft_store.store_client import StoreClient, WebBrowserWaitingInteractor


def _fake_response(status_code, reason=None, json=None):
    response = Mock(spec="requests.Response")
    response.status_code = status_code
    response.ok = status_code == 200
    response.reason = reason
    if json is not None:
        response.json = Mock(return_value=json)
    return response


@pytest.fixture
def real_macaroon():
    return json.dumps(
        {
            "s64": "a0Vi7CwhHWjS4bxzKPhCZQIEJDvlbh9FyhOtWx0tNFQ",
            "c": [
                {"i": "time-before 2022-03-18T19:54:57.151721Z"},
                {
                    "v64": "pDqaL9KDrPfCQCLDUdPc8yO2bTQheWGsM1tpxRaS_4BT3r6zpdnT5TelXz8vpjb4iUhTnc60-x5DPKJOpRuwAi4qMdNa67Vo",
                    "l": "https://api.jujucharms.com/identity/",
                    "i64": "AoZh2j7mbDQgh3oK3qMqoXKKFAnJvmOKwmDCNYHIxHqQnFLJZJUBpqoiJtqra-tyXPPMUTmfuXMgOWP7xKwTD26FBgtJBdh1mE1wt3kf0Ur_TnOzbAWQCHKxqK9jAp1jYv-LlLLAlQAmoqvz9fBf2--dIxHiLIRTThmAESAnlLZHOJ7praDmIScsLQC475a85avA",
                },
            ],
            "l": "api.snapcraft.io",
            "i64": "AwoQ2Ft5YBjnovqdr8VNV3TSlhIBMBoOCgVsb2dpbhIFbG9naW4",
        }
    )


@pytest.fixture
def http_client_request_mock(real_macaroon):
    def request(*args, **kwargs):  # pylint: disable=W0613
        if args[1] == "POST" and "tokens" in args[2]:
            response = _fake_response(200, json={"macaroon": real_macaroon})
        elif args[1] == "GET" and "whoami" in args[2]:
            response = _fake_response(
                200,
                json={"name": "Fake Person", "username": "fakeuser", "id": "fake-id"},
            )
        else:
            response = _fake_response(200)

        return response

    patched_http_client = patch(
        "craft_store.store_client.HTTPClient.request",
        autospec=True,
        side_effect=request,
    )
    mocked_http_client = patched_http_client.start()
    yield mocked_http_client
    patched_http_client.stop()


@pytest.fixture
def bakery_discharge_mock(monkeypatch):
    token_response_mock = _fake_response(
        200, json={"kind": "kind", "token": "TOKEN", "token64": b"VE9LRU42NA=="}
    )
    monkeypatch.setattr(
        httpbakery.Client, "acquire_discharge", lambda: token_response_mock
    )

    def mock_discharge(*args, **kwargs):  # pylint: disable=W0613
        return [
            Macaroon(
                location="fake-server.com",
                signature="d9533461d7835e4851c7e3b639144406cf768597dea6e133232fbd2385a5c050",
            )
        ]

    monkeypatch.setattr(bakery, "discharge_all", mock_discharge)


@pytest.fixture
def auth_mock(real_macaroon):
    patched_auth = patch("craft_store.store_client.Auth", autospec=True)
    mocked_auth = patched_auth.start()
    mocked_auth.return_value.get_credentials.return_value = real_macaroon
    mocked_auth.return_value.encode_credentials.return_value = "c2VjcmV0LWtleXM="
    yield mocked_auth
    patched_auth.stop()


@pytest.mark.usefixtures("bakery_discharge_mock")
@pytest.mark.parametrize("environment_auth", (None, "APPLICATION_CREDENTIALS"))
def test_store_client_login(
    monkeypatch,
    http_client_request_mock,
    real_macaroon,
    auth_mock,
    environment_auth,
):
    if environment_auth is not None:
        monkeypatch.setenv(environment_auth, "c2VjcmV0LWtleXM=")

    store_client = StoreClient(
        base_url="https://fake-server.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
        environment_auth=environment_auth,
    )

    save_credentials = environment_auth is None
    credentials = store_client.login(
        permissions=["perm-1", "perm-2"],
        description="fakecraft@foo",
        ttl=60,
        save_credentials=save_credentials,
    )

    assert credentials == "c2VjcmV0LWtleXM="
    assert http_client_request_mock.mock_calls == [
        call(
            store_client,
            "POST",
            "https://fake-server.com/v1/tokens",
            json={
                "permissions": ["perm-1", "perm-2"],
                "description": "fakecraft@foo",
                "ttl": 60,
            },
        ),
        call(
            store_client,
            "POST",
            "https://fake-server.com/v1/tokens/exchange",
            headers={
                "Macaroons": "W3siaWRlbnRpZmllciI6ICIiLCAic2lnbmF0dXJlIjogImQ5NTMzNDYxZDc4MzVlNDg1MWM3ZTNiNjM5MTQ0NDA2Y2Y3Njg1OTdkZWE2ZTEzMzIzMmZiZDIzODVhNWMwNTAiLCAibG9jYXRpb24iOiAiZmFrZS1zZXJ2ZXIuY29tIn1d"
            },
            json={},
        ),
    ]

    if save_credentials:
        expected_auth_calls = [
            call(
                "fakecraft",
                "https://fake-server.com",
                environment_auth=environment_auth,
            ),
            call().set_credentials(real_macaroon),
            call().encode_credentials(real_macaroon),
        ]
    else:
        expected_auth_calls = [
            call(
                "fakecraft",
                "https://fake-server.com",
                environment_auth=environment_auth,
            ),
            call().encode_credentials(real_macaroon),
        ]

    assert auth_mock.mock_calls == expected_auth_calls


def test_store_client_login_with_packages_and_channels(
    http_client_request_mock, real_macaroon, bakery_discharge_mock, auth_mock
):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    credentials = store_client.login(
        permissions=["perm-1", "perm-2"],
        description="fakecraft@foo",
        ttl=60,
        channels=["edge"],
        packages=[
            endpoints.Package("my-charm", "charm"),
            endpoints.Package("my-bundle", "bundle"),
        ],
    )

    assert credentials == "c2VjcmV0LWtleXM="
    assert http_client_request_mock.mock_calls == [
        call(
            store_client,
            "POST",
            "https://fake-server.com/v1/tokens",
            json={
                "permissions": ["perm-1", "perm-2"],
                "description": "fakecraft@foo",
                "ttl": 60,
                "packages": [
                    {
                        "name": "my-charm",
                        "type": "charm",
                    },
                    {
                        "name": "my-bundle",
                        "type": "bundle",
                    },
                ],
                "channels": ["edge"],
            },
        ),
        call(
            store_client,
            "POST",
            "https://fake-server.com/v1/tokens/exchange",
            headers={
                "Macaroons": "W3siaWRlbnRpZmllciI6ICIiLCAic2lnbmF0dXJlIjogImQ5NTMzNDYxZDc4MzVlNDg1MWM3ZTNiNjM5MTQ0NDA2Y2Y3Njg1OTdkZWE2ZTEzMzIzMmZiZDIzODVhNWMwNTAiLCAibG9jYXRpb24iOiAiZmFrZS1zZXJ2ZXIuY29tIn1d"
            },
            json={},
        ),
    ]

    assert auth_mock.mock_calls == [
        call("fakecraft", "https://fake-server.com", environment_auth=None),
        call().set_credentials(real_macaroon),
        call().encode_credentials(real_macaroon),
    ]


def test_store_client_login_store_raises_with_environment_auth(monkeypatch):
    monkeypatch.setenv("CREDENTIALS", "c2VjcmV0LWtleXM=")

    store_client = StoreClient(
        base_url="https://fake-server.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
        environment_auth="CREDENTIALS",
    )

    with pytest.raises(RuntimeError) as error:
        store_client.login(
            permissions=["perm-1", "perm-2"],
            description="fakecraft@foo",
            ttl=60,
            save_credentials=True,
        )

    assert (
        str(error.value) == "Cannot use save_credentials when environment_auth is set."
    )


def test_store_client_logout(auth_mock):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    store_client.logout()

    assert auth_mock.mock_calls == [
        call("fakecraft", "https://fake-server.com", environment_auth=None),
        call().del_credentials(),
    ]


def test_store_client_logout_raises_with_environment_auth(monkeypatch):
    monkeypatch.setenv("CREDENTIALS", "c2VjcmV0LWtleXM=")

    store_client = StoreClient(
        base_url="https://fake-server.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
        environment_auth="CREDENTIALS",
    )

    with pytest.raises(RuntimeError) as error:
        store_client.logout()

    assert str(error.value) == "Cannot logout with environment_auth."


def test_store_client_request(http_client_request_mock, real_macaroon, auth_mock):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    store_client.request("GET", "https://fake-server.com/fakepath")

    assert http_client_request_mock.mock_calls == [
        call(
            store_client,
            "GET",
            "https://fake-server.com/fakepath",
            params=None,
            headers={"Authorization": f"Macaroon {real_macaroon}"},
        )
    ]

    assert auth_mock.mock_calls == [
        call("fakecraft", "https://fake-server.com", environment_auth=None),
        call().get_credentials(),
    ]


def test_store_client_whoami(http_client_request_mock, real_macaroon, auth_mock):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        endpoints=endpoints.CHARMHUB,
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
            store_client,
            "GET",
            "https://fake-server.com/v1/whoami",
            params=None,
            headers={"Authorization": f"Macaroon {real_macaroon}"},
        )
    ]

    assert auth_mock.mock_calls == [
        call("fakecraft", "https://fake-server.com", environment_auth=None),
        call().get_credentials(),
    ]


def test_webinteractore_wait_for_token(http_client_request_mock):
    http_client_request_mock.side_effect = None
    http_client_request_mock.return_value = _fake_response(
        200, json={"kind": "kind", "token": "TOKEN", "token64": b"VE9LRU42NA=="}
    )

    wbi = WebBrowserWaitingInteractor(user_agent="foobar")

    discharged_token = wbi._wait_for_token(  # pylint: disable=W0212
        object(), "https://foo.bar/candid"
    )

    assert discharged_token == httpbakery.DischargeToken(kind="kind", value="TOKEN")
    assert http_client_request_mock.mock_calls == [
        call(ANY, "GET", "https://foo.bar/candid")
    ]


def test_webinteractore_wait_for_token_timeout_error(http_client_request_mock):
    http_client_request_mock.side_effect = None
    http_client_request_mock.return_value = _fake_response(400, json={})

    wbi = WebBrowserWaitingInteractor(user_agent="foobar")

    with pytest.raises(errors.CandidTokenTimeoutError):
        wbi._wait_for_token(object(), "https://foo.bar/candid")  # pylint: disable=W0212


def test_webinteractore_wait_for_token_kind_error(http_client_request_mock):
    http_client_request_mock.side_effect = None
    http_client_request_mock.return_value = _fake_response(200, json={})

    wbi = WebBrowserWaitingInteractor(user_agent="foobar")

    with pytest.raises(errors.CandidTokenKindError):
        wbi._wait_for_token(object(), "https://foo.bar/candid")  # pylint: disable=W0212


def test_webinteractore_wait_for_token_value_error(http_client_request_mock):
    http_client_request_mock.side_effect = None
    http_client_request_mock.return_value = _fake_response(
        200,
        json={
            "kind": "kind",
        },
    )

    wbi = WebBrowserWaitingInteractor(user_agent="foobar")

    with pytest.raises(errors.CandidTokenValueError):
        wbi._wait_for_token(object(), "https://foo.bar/candid")  # pylint: disable=W0212
