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

from unittest import mock

import pytest
import requests
import urllib3  # type: ignore

from craft_store import errors


def _fake_error_response(status_code, reason):
    response = mock.Mock()
    response.status_code = status_code
    response.reason = reason
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
                urllib3.exceptions.MaxRetryError(pool="test-pool", url="test-url")
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
)


@pytest.mark.parametrize("scenario", scenarios)
def test_error_formatting(scenario):
    assert (
        str(scenario["exception_class"](*scenario["args"]))
        == scenario["expected_message"]
    )
