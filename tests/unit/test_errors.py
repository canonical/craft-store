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

from textwrap import dedent
from unittest import mock

import pytest
import requests
import urllib3
import urllib3.exceptions
from craft_store import errors
from requests.exceptions import JSONDecodeError


def _fake_error_response(status_code, reason, json=None):
    response = mock.Mock()
    response.status_code = status_code
    response.reason = reason
    if json is None:
        response.json.side_effect = JSONDecodeError("foo", "doc", 0)
    else:
        response.json = mock.Mock(return_value=json)

    return response


scenarios = (
    {
        "exception_class": errors.NetworkError,
        "args": [requests.exceptions.ConnectionError("bad error")],
        "expected_message": "bad error",
    },
    {
        "exception_class": errors.NetworkError,
        "args": [
            requests.exceptions.ConnectionError(
                urllib3.exceptions.MaxRetryError(
                    pool=urllib3.connectionpool.ConnectionPool("https://foo.bar"),
                    url="test-url",
                )
            )
        ],
        "expected_message": "Maximum retries exceeded trying to reach the store.",
    },
    {
        "exception_class": errors.StoreServerError,
        "args": [_fake_error_response(500, "internal server error")],
        "expected_message": "Issue encountered while processing your request: [500] internal server error.",
    },
    {
        "exception_class": errors.StoreServerError,
        "args": [_fake_error_response(501, "not implemented")],
        "expected_message": "Issue encountered while processing your request: [501] not implemented.",
    },
    {
        "exception_class": errors.NoKeyringError,
        "args": [],
        "expected_message": "No keyring found to store or retrieve credentials from.",
    },
    {
        "exception_class": errors.KeyringUnlockError,
        "args": [],
        "expected_message": "Failed to unlock the keyring.",
    },
    {
        "exception_class": errors.CredentialsAlreadyAvailable,
        "args": ["mycraft", "my.host.com"],
        "expected_message": "Credentials found for 'mycraft' on 'my.host.com'.",
    },
    {
        "exception_class": errors.CredentialsUnavailable,
        "args": ["mycraft", "my.host.com"],
        "expected_message": "No credentials found for 'mycraft' on 'my.host.com'.",
    },
    {
        "exception_class": errors.CredentialsNotParseable,
        "args": [],
        "expected_message": "Credentials could not be parsed. Expected base64 encoded credentials.",
    },
    {
        "exception_class": errors.CandidTokenTimeoutError,
        "args": ["https://foo.bar"],
        "expected_message": "Timed out waiting for token response from 'https://foo.bar'.",
    },
    {
        "exception_class": errors.CandidTokenKindError,
        "args": ["https://foo.bar"],
        "expected_message": "Empty token kind returned from 'https://foo.bar'.",
    },
    {
        "exception_class": errors.CandidTokenValueError,
        "args": ["https://foo.bar"],
        "expected_message": "Empty token value returned from 'https://foo.bar'.",
    },
)


@pytest.mark.parametrize("scenario", scenarios)
def test_error_formatting(scenario):
    assert (
        str(scenario["exception_class"](*scenario["args"]))
        == scenario["expected_message"]
    )


error_lists = [
    {
        "error_list": [
            {"code": "resource-not-found", "message": "could not find resource"},
        ],
        "expected": dedent(
            """\
            Store operation failed:
            - resource-not-found: could not find resource"""
        ),
    },
    {
        "error_list": [
            {"code": "resource-not-found", "message": "could not find resource"},
            {
                "code": "resource-doubly-not-found",
                "message": "could not find resource when trying harder",
            },
        ],
        "expected": dedent(
            """\
            Store operation failed:
            - resource-not-found: could not find resource
            - resource-doubly-not-found: could not find resource when trying harder"""
        ),
    },
]


@pytest.mark.parametrize("error_list_key", ["error-list", "error_list"])
@pytest.mark.parametrize("error_list", error_lists)
def test_store_error_list(error_list_key, error_list):
    response = _fake_error_response(
        404, "resource-not-found", json={error_list_key: error_list["error_list"]}
    )
    assert str(errors.StoreServerError(response)) == error_list["expected"]


@pytest.mark.parametrize("missing", ["code", "message"])
@pytest.mark.parametrize("error_list_key", ["error-list", "error_list"])
def test_store_error_list_missing_element(missing, error_list_key):
    error_list = [
        {"code": "resource-not-found", "message": "could not find resource"},
    ]
    error_list[0].pop(missing)
    response = _fake_error_response(
        404, "resource-not-found", json={error_list_key: error_list}
    )
    assert (
        str(errors.StoreServerError(response))
        == "Issue encountered while processing your request: [404] resource-not-found."
    )
