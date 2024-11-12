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
from craft_store import Auth, base_client, creds, endpoints, errors
from craft_store.store_client import StoreClient, WebBrowserWaitingInteractor
from macaroonbakery import bakery, httpbakery
from pymacaroons.macaroon import Macaroon


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
    def request(*args, **kwargs):  # noqa: ARG001
        if args[1] == "POST" and "tokens" in args[2]:
            response = _fake_response(200, json={"macaroon": real_macaroon})
        elif args[1] == "GET" and "whoami" in args[2]:
            response = _fake_response(
                200,
                json={"name": "Fake Person", "username": "fakeuser", "id": "fake-id"},
            )
        elif args[1] == "POST" and args[2] in (
            "https://fake-charm-storage.com/unscanned-upload/",
            "https://fake-snap-storage.com/unscanned-upload/",
        ):
            response = _fake_response(
                200,
                json={"upload_id": "12345", "successful": True},
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
def _bakery_discharge_mock(monkeypatch):
    token_response_mock = _fake_response(
        200, json={"kind": "kind", "token": "TOKEN", "token64": b"VE9LRU42NA=="}
    )
    monkeypatch.setattr(
        httpbakery.Client, "acquire_discharge", lambda: token_response_mock
    )

    def mock_discharge(*args, **kwargs):  # noqa: ARG001
        return [
            Macaroon(
                location="fake-server.com",
                signature="d9533461d7835e4851c7e3b639144406cf768597dea6e133232fbd2385a5c050",
            )
        ]

    monkeypatch.setattr(bakery, "discharge_all", mock_discharge)


@pytest.fixture
def auth_mock(real_macaroon, new_auth):
    patched_auth = patch("craft_store.base_client.Auth", autospec=True)
    mocked_auth = patched_auth.start()

    wrapped_credentials = creds.marshal_candid_credentials(real_macaroon)
    stored_credentials = wrapped_credentials if new_auth else real_macaroon

    mocked_auth.return_value.get_credentials.return_value = stored_credentials
    mocked_auth.return_value.encode_credentials.return_value = "c2VjcmV0LWtleXM="
    yield mocked_auth
    patched_auth.stop()


@pytest.mark.usefixtures("_bakery_discharge_mock")
@pytest.mark.parametrize("ephemeral_auth", [True, False])
@pytest.mark.parametrize("environment_auth", [None, "APPLICATION_CREDENTIALS"])
@pytest.mark.parametrize("file_fallback", [True, False])
def test_store_client_login(
    http_client_request_mock,
    real_macaroon,
    auth_mock,
    environment_auth,
    ephemeral_auth,
    file_fallback,
):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
        environment_auth=environment_auth,
        ephemeral=ephemeral_auth,
        file_fallback=file_fallback,
    )

    credentials = store_client.login(
        permissions=["perm-1", "perm-2"], description="fakecraft@foo", ttl=60
    )

    assert credentials == "c2VjcmV0LWtleXM="
    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "POST",
            "https://fake-server.com/v1/tokens",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "permissions": ["perm-1", "perm-2"],
                "description": "fakecraft@foo",
                "ttl": 60,
            },
        ),
        call(
            store_client.http_client,
            "POST",
            "https://fake-server.com/v1/tokens/exchange",
            headers={
                "Macaroons": "W3siaWRlbnRpZmllciI6ICIiLCAic2lnbmF0dXJlIjogImQ5NTMzNDYxZDc4MzVlNDg1MWM3ZTNiNjM5MTQ0NDA2Y2Y3Njg1OTdkZWE2ZTEzMzIzMmZiZDIzODVhNWMwNTAiLCAibG9jYXRpb24iOiAiZmFrZS1zZXJ2ZXIuY29tIn1d"
            },
            json={},
        ),
    ]

    wrapped = creds.marshal_candid_credentials(real_macaroon)

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=environment_auth,
            ephemeral=ephemeral_auth,
            file_fallback=file_fallback,
        ),
        call().ensure_no_credentials(),
        call().set_credentials(wrapped),
        call().encode_credentials(wrapped),
    ]


@pytest.mark.usefixtures("_bakery_discharge_mock")
def test_store_client_login_with_packages_and_channels(
    http_client_request_mock, real_macaroon, auth_mock
):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
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
            store_client.http_client,
            "POST",
            "https://fake-server.com/v1/tokens",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
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
            store_client.http_client,
            "POST",
            "https://fake-server.com/v1/tokens/exchange",
            headers={
                "Macaroons": "W3siaWRlbnRpZmllciI6ICIiLCAic2lnbmF0dXJlIjogImQ5NTMzNDYxZDc4MzVlNDg1MWM3ZTNiNjM5MTQ0NDA2Y2Y3Njg1OTdkZWE2ZTEzMzIzMmZiZDIzODVhNWMwNTAiLCAibG9jYXRpb24iOiAiZmFrZS1zZXJ2ZXIuY29tIn1d"
            },
            json={},
        ),
    ]

    expected_credentials = creds.marshal_candid_credentials(real_macaroon)

    assert auth_mock.mock_calls == [
        call(
            "fakecraft",
            "fake-server.com",
            environment_auth=None,
            ephemeral=False,
            file_fallback=False,
        ),
        call().ensure_no_credentials(),
        call().set_credentials(expected_credentials),
        call().encode_credentials(expected_credentials),
    ]


def test_store_client_logout(auth_mock):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        endpoints=endpoints.CHARMHUB,
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


def test_store_client_request(http_client_request_mock, real_macaroon, auth_mock):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        endpoints=endpoints.CHARMHUB,
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
            headers={"Authorization": f"Macaroon {real_macaroon}"},
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


def test_store_client_whoami(http_client_request_mock, real_macaroon, auth_mock):
    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
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
            store_client.http_client,
            "GET",
            "https://fake-server.com/v1/tokens/whoami",
            params=None,
            headers={"Authorization": f"Macaroon {real_macaroon}"},
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


@pytest.mark.parametrize("hub", [endpoints.CHARMHUB, endpoints.SNAP_STORE])
def test_store_client_upload_file_no_monitor(tmp_path, http_client_request_mock, hub):
    if hub == endpoints.CHARMHUB:
        storage_url = "https://fake-charm-storage.com"
    else:
        storage_url = "https://fake-snap-storage.com"

    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url=storage_url,
        endpoints=hub,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    filepath = tmp_path / "artifact.thing"
    filepath.touch()

    assert store_client.upload_file(filepath=filepath) == "12345"
    store_client.upload_file(filepath=filepath)
    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "POST",
            f"{storage_url}/unscanned-upload/",
            headers={
                "Content-Type": ANY,
                "Accept": "application/json",
            },
            data=ANY,
        ),
        call(
            store_client.http_client,
            "POST",
            f"{storage_url}/unscanned-upload/",
            headers={
                "Content-Type": ANY,
                "Accept": "application/json",
            },
            data=ANY,
        ),
    ]


@pytest.mark.parametrize("hub", [endpoints.CHARMHUB, endpoints.SNAP_STORE])
def test_store_client_upload_file_with_monitor(tmp_path, http_client_request_mock, hub):
    if hub == endpoints.CHARMHUB:
        storage_url = "https://fake-charm-storage.com"
    else:
        storage_url = "https://fake-snap-storage.com"

    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url=storage_url,
        endpoints=hub,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
    )

    filepath = tmp_path / "artifact.thing"
    filepath.write_text("file to upload")

    def callback(monitor):
        pass

    def monitor(encoder):  # noqa: ARG001
        return callback

    with patch("craft_store.base_client.MultipartEncoder"):
        with patch(
            "craft_store.base_client.MultipartEncoderMonitor",
            wraps=base_client.MultipartEncoderMonitor,
        ) as wrapped_encoder_monitor:
            assert (
                store_client.upload_file(filepath=filepath, monitor_callback=monitor)
                == "12345"
            )
            assert wrapped_encoder_monitor.mock_calls == [
                call(
                    base_client.MultipartEncoder(
                        {
                            "binary": (
                                "artifact.thing",
                                ANY,
                                "application/octect-stream",
                            )
                        },
                    ),
                    monitor(monitor),
                )
            ]

    store_client.upload_file(filepath=filepath)
    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "POST",
            f"{storage_url}/unscanned-upload/",
            headers={
                "Content-Type": ANY,
                "Accept": "application/json",
            },
            data=ANY,
        ),
        call(
            store_client.http_client,
            "POST",
            f"{storage_url}/unscanned-upload/",
            headers={
                "Content-Type": ANY,
                "Accept": "application/json",
            },
            data=ANY,
        ),
    ]


def test_webinteractore_wait_for_token(http_client_request_mock):
    http_client_request_mock.side_effect = None
    http_client_request_mock.return_value = _fake_response(
        200, json={"kind": "kind", "token": "TOKEN", "token64": b"VE9LRU42NA=="}
    )

    wbi = WebBrowserWaitingInteractor(user_agent="foobar")

    discharged_token = wbi._wait_for_token(None, "https://foo.bar/candid")

    assert discharged_token == httpbakery.DischargeToken(kind="kind", value="TOKEN")
    assert http_client_request_mock.mock_calls == [
        call(ANY, "GET", "https://foo.bar/candid")
    ]


def test_webinteractore_wait_for_token_timeout_error(
    http_client_request_mock,
):
    http_client_request_mock.side_effect = None
    http_client_request_mock.return_value = _fake_response(400, json={})

    wbi = WebBrowserWaitingInteractor(user_agent="foobar")

    with pytest.raises(errors.CandidTokenTimeoutError):
        wbi._wait_for_token(None, "https://foo.bar/candid")


def test_webinteractore_wait_for_token_kind_error(http_client_request_mock):
    http_client_request_mock.side_effect = None
    http_client_request_mock.return_value = _fake_response(200, json={})

    wbi = WebBrowserWaitingInteractor(user_agent="foobar")

    with pytest.raises(errors.CandidTokenKindError):
        wbi._wait_for_token(None, "https://foo.bar/candid")


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
        wbi._wait_for_token(None, "https://foo.bar/candid")


def test_store_client_env_var(http_client_request_mock, new_auth, monkeypatch):
    """
    Test StoreClient credential handling when using auth from an environment variable.
    """

    # The auth environment variable contents must have the same format as those stored
    # by Auth.set_credentials(): some payload, base64-encoded. So we "manually" encode
    # a serialized dummy macaroon.
    macaroon = Macaroon(
        location="fake-server.com",
        signature="d9533461d7835e4851c7e3b639144406cf768597dea6e133232fbd2385a5c050",
    )
    credentials = macaroon.serialize()

    if new_auth:
        # new, type-tagged auth: use the dict tagging the type and the actual payload
        # (the serialized macaroon).
        wrapped_credentials = creds.marshal_candid_credentials(credentials)
        stored_b64_credentials = Auth.encode_credentials(wrapped_credentials)
    else:
        # old auth: use the serialized macaroon "as-is".
        stored_b64_credentials = Auth.encode_credentials(credentials)

    environment_auth = "CRAFT_AUTH_TEST_VAR"
    monkeypatch.setenv(environment_auth, stored_b64_credentials)

    # This StoreClient uses a non-mocked Auth with a memory keyring because of `environment_auth`.
    store_client = StoreClient(
        base_url="https://fake-server.com",
        storage_base_url="https://fake-storage.com",
        endpoints=endpoints.CHARMHUB,
        application_name="fakecraft",
        user_agent="FakeCraft Unix X11",
        environment_auth=environment_auth,
    )

    # Make a (mocked) network request to check the provided credentials.
    assert store_client.whoami() == {
        "name": "Fake Person",
        "username": "fakeuser",
        "id": "fake-id",
    }

    # When making the request the Authorization header must contain the original
    # serialized (non-base64-encoded) macaroon, regardless of new or old auth.
    assert http_client_request_mock.mock_calls == [
        call(
            store_client.http_client,
            "GET",
            "https://fake-server.com/v1/tokens/whoami",
            params=None,
            headers={"Authorization": f"Macaroon {credentials}"},
        )
    ]
