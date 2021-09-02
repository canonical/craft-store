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
import urllib3  # type: ignore

from craft_store import HTTPClient, errors


def _fake_error_response(status_code, reason):
    response = Mock(spec="requests.Response")
    response.status_code = status_code
    response.reason = reason
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
        total=10, backoff_factor=2, status_forcelist=[104, 500, 502, 503, 504]
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
        total=20, backoff_factor=10, status_forcelist=[104, 500, 502, 503, 504]
    )


def test_session_bad_total_environment(monkeypatch, caplog, session_mock, retry_mock):
    monkeypatch.setenv("CRAFT_STORE_RETRIES", "NaN")
    caplog.set_level(logging.DEBUG)

    HTTPClient(user_agent="Secret Agent")

    assert [
        call("http://", ANY),
        call("https://", ANY),
    ] in session_mock().mount.mock_calls
    retry_mock.assert_called_once_with(
        total=10, backoff_factor=2, status_forcelist=[104, 500, 502, 503, 504]
    )
    assert ["CRAFT_STORE_RETRIES is not se to an integer, using default of 10."] == [
        rec.message for rec in caplog.records
    ]


def test_session_bad_backoff_environment(monkeypatch, caplog, session_mock, retry_mock):
    monkeypatch.setenv("CRAFT_STORE_BACKOFF", "NaN")
    caplog.set_level(logging.DEBUG)

    HTTPClient(user_agent="Secret Agent")

    assert [
        call("http://", ANY),
        call("https://", ANY),
    ] in session_mock().mount.mock_calls
    retry_mock.assert_called_once_with(
        total=10, backoff_factor=2, status_forcelist=[104, 500, 502, 503, 504]
    )
    assert ["CRAFT_STORE_BACKOFF is not se to an integer, using default of 2."] == [
        rec.message for rec in caplog.records
    ]


@pytest.mark.parametrize("method", ("get", "post", "put"))
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
    fake_response = _fake_error_response(503, "cannot reach server")
    session_mock().request.return_value = fake_response

    with pytest.raises(errors.StoreServerError) as store_error:
        HTTPClient(user_agent="Secret Agent").request(
            "GET",
            "https://foo.bar",
        )
        assert store_error.response == fake_response  # type: ignore


def test_request_connection_error(session_mock):
    connection_error = requests.exceptions.ConnectionError(
        urllib3.exceptions.MaxRetryError(pool="test-pool", url="test-url")
    )
    session_mock().request.side_effect = connection_error

    with pytest.raises(errors.NetworkError) as network_error:
        HTTPClient(user_agent="Secret Agent").request(
            "GET",
            "https://foo.bar",
        )
        assert network_error.__cause__ == connection_error  # type: ignore


def test_request_retry_error(session_mock):
    retry_error = requests.exceptions.RetryError()
    session_mock().request.side_effect = retry_error

    with pytest.raises(errors.NetworkError) as network_error:
        HTTPClient(user_agent="Secret Agent").request(
            "GET",
            "https://foo.bar",
        )
        assert network_error.__cause__ == retry_error  # type: ignore
