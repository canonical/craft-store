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
from unittest.mock import ANY, Mock, call, patch

import pytest
import requests
import urllib3
import urllib3.exceptions
from craft_store import HTTPClient, errors
from craft_store.http_client import _get_retry_value
from requests.exceptions import JSONDecodeError


def _fake_error_response(status_code, reason, json_raises=False):
    response = Mock()
    response.status_code = status_code
    response.ok = status_code == 200
    response.reason = reason
    if json_raises:
        response.json.side_effect = JSONDecodeError("foo", "doc", 0)
    return response


@pytest.fixture
def session_mock():
    patched_session = patch("requests.Session", autospec=True)
    mocked_session = patched_session.start()
    mocked_session().request.return_value = _fake_error_response(200, "")
    yield mocked_session
    patched_session.stop()


@pytest.fixture
def retry_mock():
    patched_retry = patch("craft_store.http_client.Retry", autospec=True)
    yield patched_retry.start()
    patched_retry.stop()


def test_session_defaults(session_mock, retry_mock):
    HTTPClient(user_agent="Secret Agent")

    assert [
        call("http://", ANY),
        call("https://", ANY),
    ] in session_mock().mount.mock_calls
    retry_mock.assert_called_once_with(
        total=8, backoff_factor=1, status_forcelist=[500, 502, 503, 504]
    )


def test_session_environment_values(monkeypatch, session_mock, retry_mock):
    monkeypatch.setenv("CRAFT_STORE_RETRIES", "20")
    monkeypatch.setenv("CRAFT_STORE_BACKOFF", "10")

    HTTPClient(user_agent="Secret Agent")

    assert [
        call("http://", ANY),
        call("https://", ANY),
    ] in session_mock().mount.mock_calls
    retry_mock.assert_called_once_with(
        total=20, backoff_factor=10, status_forcelist=[500, 502, 503, 504]
    )


@pytest.mark.parametrize("method", ["get", "post", "put"])
def test_methods(session_mock, method):
    client = HTTPClient(user_agent="Secret Agent")
    getattr(client, method)("https://foo.bar")

    assert session_mock().request.mock_calls == [
        call(
            method.upper(),
            "https://foo.bar",
            headers={"User-Agent": "Secret Agent"},
            params=None,
        )
    ]


scenarios = [
    {
        "expected_params": None,
        "expected_headers": {"User-Agent": "Secret Agent"},
        "expected_logger_debug_tail": "None and headers {'User-Agent': 'Secret Agent'}",
    },
    {
        "kwargs": {"headers": {"foo": "bar"}},
        "expected_params": None,
        "expected_headers": {"User-Agent": "Secret Agent", "foo": "bar"},
        "expected_logger_debug_tail": "None and headers {'foo': 'bar', 'User-Agent': 'Secret Agent'}",
    },
    {
        "kwargs": {"headers": {"Authorization": "bar"}},
        "expected_params": None,
        "expected_headers": {
            "User-Agent": "Secret Agent",
            "Authorization": "bar",
        },
        "expected_logger_debug_tail": (
            "None and headers {'Authorization': '<macaroon>', 'User-Agent': 'Secret Agent'}"
        ),
    },
    {
        "kwargs": {"headers": {"Macaroons": "bar"}},
        "expected_params": None,
        "expected_headers": {
            "User-Agent": "Secret Agent",
            "Macaroons": "bar",
        },
        "expected_logger_debug_tail": "None and headers {'Macaroons': '<macaroon>', 'User-Agent': 'Secret Agent'}",
    },
    {
        "kwargs": {"params": {"query": "bar"}},
        "expected_params": {"query": "bar"},
        "expected_headers": {
            "User-Agent": "Secret Agent",
        },
        "expected_logger_debug_tail": "{'query': 'bar'} and headers {'User-Agent': 'Secret Agent'}",
    },
    {
        "kwargs": {"params": {"query": "bar"}},
        "expected_params": {"query": "bar"},
        "expected_headers": {
            "User-Agent": "Secret Agent",
        },
        "expected_logger_debug_tail": "{'query': 'bar'} and headers {'User-Agent': 'Secret Agent'}",
    },
]


@pytest.mark.parametrize("scenario", scenarios)
def test_request(caplog, session_mock, scenario):
    caplog.set_level(logging.DEBUG)

    HTTPClient(user_agent="Secret Agent").request(
        "UPDATE",
        "https://foo.bar",
        **scenario.get("kwargs", {}),
    )

    assert session_mock().request.mock_calls == [
        call(
            "UPDATE",
            "https://foo.bar",
            headers=scenario["expected_headers"],
            params=scenario["expected_params"],
        )
    ]
    assert [
        "HTTP 'UPDATE' for 'https://foo.bar' with params "
        + scenario["expected_logger_debug_tail"]
    ] == [rec.message for rec in caplog.records]


def test_request_500(session_mock):
    fake_response = _fake_error_response(503, "cannot reach server", json_raises=True)
    session_mock().request.return_value = fake_response

    with pytest.raises(errors.StoreServerError) as store_error:
        HTTPClient(user_agent="Secret Agent").request(
            "GET",
            "https://foo.bar",
        )

    assert store_error.value.response == fake_response


def test_request_connection_error(session_mock):
    connection_pool = urllib3.connectionpool.ConnectionPool("https://foo.bar")
    connection_error = requests.exceptions.ConnectionError(
        urllib3.exceptions.MaxRetryError(pool=connection_pool, url="test-url")
    )
    session_mock().request.side_effect = connection_error

    with pytest.raises(errors.NetworkError) as network_error:
        HTTPClient(user_agent="Secret Agent").request(
            "GET",
            "https://foo.bar",
        )

    assert network_error.value.__cause__ == connection_error


def test_request_retry_error(session_mock):
    retry_error = requests.exceptions.RetryError()
    session_mock().request.side_effect = retry_error

    with pytest.raises(errors.NetworkError) as network_error:
        HTTPClient(user_agent="Secret Agent").request(
            "GET",
            "https://foo.bar",
        )

    assert network_error.value.__cause__ == retry_error


@pytest.mark.parametrize("environment_value", ["0", "10", "20000"])
def test_get_retry_value_environment_override(monkeypatch, caplog, environment_value):
    monkeypatch.setenv("FAKE_ENV", environment_value)
    caplog.set_level(logging.DEBUG)

    assert _get_retry_value("FAKE_ENV", 0) == int(environment_value)
    assert len(caplog.records) == 0


@pytest.mark.parametrize(
    ("environment_value", "default"), [("NaN", 10), ("NaN", 0.4), ("foo", 1)]
)
def test_get_retry_value_not_a_number_returns_default(
    monkeypatch, caplog, environment_value, default
):
    monkeypatch.setenv("FAKE_ENV", environment_value)
    caplog.set_level(logging.DEBUG)

    assert _get_retry_value("FAKE_ENV", default) == default
    assert [
        f"'FAKE_ENV' set to invalid value {environment_value!r}, setting to {default}."
    ] == [rec.message for rec in caplog.records]


@pytest.mark.parametrize(("environment_value", "default"), [("-1", 10), ("-1000", 0.4)])
def test_get_retry_value_negative_number_returns_default(
    monkeypatch, caplog, environment_value, default
):
    monkeypatch.setenv("FAKE_ENV", environment_value)
    caplog.set_level(logging.DEBUG)

    assert _get_retry_value("FAKE_ENV", default) == default
    int_value = int(environment_value)
    assert [
        f"'FAKE_ENV' set to non positive value {int_value!r}, setting to {default}."
    ] == [rec.message for rec in caplog.records]
