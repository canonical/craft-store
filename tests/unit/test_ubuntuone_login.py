# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2026 Canonical Ltd.
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

import pytest
import pytest_httpx
from craft_store import Auth, errors
from craft_store.login import UbuntuOneLogin
from pymacaroons import Macaroon


def _make_root() -> Macaroon:
    root = Macaroon(
        location="api.example.test",
        identifier="root",
        key="root-key",
    )
    root.add_third_party_caveat(
        "login.ubuntu.com",
        "login-key",
        "login-caveat",
    )
    return root


def test_login_with_raises_when_otp_missing(
    httpx_mock: pytest_httpx.HTTPXMock,
    mock_auth,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.example.test/v1/tokens/usso",
        json={"macaroon": _make_root().serialize()},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://login.ubuntu.com/api/v2/tokens/discharge",
        status_code=401,
        json={
            "code": "TWOFACTOR_REQUIRED",
            "message": "OTP required",
            "error_list": [{"code": "twofactor-required", "message": "OTP required"}],
        },
    )

    login = UbuntuOneLogin(
        "https://api.example.test",
        login_url="https://login.ubuntu.com",
        store_auth=mock_auth,
    )

    with pytest.raises(errors.UbuntuOneOtpRequiredError, match="account requires"):
        login.login_with(
            email="user@example.com",
            password="correct-password",  # noqa: S106
            permissions=["account-view-packages"],
        )


@pytest.mark.parametrize("otp", ["123456"])
def test_login_with_raises_on_bad_credentials(
    httpx_mock: pytest_httpx.HTTPXMock,
    otp: str,
    mock_auth,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url="https://api.example.test/v1/tokens/usso",
        json={"macaroon": _make_root().serialize()},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://login.ubuntu.com/api/v2/tokens/discharge",
        status_code=401,
        json={
            "code": "INVALID_DATA",
            "message": "Invalid request data",
            "error_list": [{"code": "invalid-data", "message": "Invalid request data"}],
        },
    )

    login = UbuntuOneLogin(
        "https://api.example.test",
        login_url="https://login.ubuntu.com",
        store_auth=mock_auth,
    )

    with pytest.raises(errors.UbuntuOneCredentialsError, match="password and OTP"):
        login.login_with(
            email="user@example.com",
            password="wrong-password",  # noqa: S106
            otp=otp,
            permissions=["account-view-packages"],
        )


def test_login_with_saves_credentials(
    httpx_mock: pytest_httpx.HTTPXMock,
    mocker,
    mock_auth,
) -> None:
    root = _make_root()
    discharge = Macaroon(
        location="login.ubuntu.com",
        identifier="discharge",
        key="discharge-key",
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.example.test/v1/tokens/usso",
        json={"macaroon": root.serialize()},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://login.ubuntu.com/api/v2/tokens/discharge",
        json={"discharge_macaroon": discharge.serialize()},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://api.example.test/v1/tokens/usso/exchange",
        json={"macaroon": "store-token"},
    )
    token_auth = mocker.Mock(spec=Auth)
    mocker.patch("craft_store.login._ubuntuone.auth.Auth", return_value=token_auth)

    login = UbuntuOneLogin(
        "https://api.example.test",
        login_url="https://login.ubuntu.com",
        store_auth=mock_auth,
    )

    login.login_with(
        email="user@example.com",
        password="correct-password",  # noqa: S106
        otp="123456",
        permissions=["account-view-packages"],
    )

    mock_auth.set_credentials.assert_called_once()
    assert mock_auth.set_credentials.call_args.kwargs == {"force": True}
    token_auth.set_credentials.assert_called_once()
    assert token_auth.set_credentials.call_args.kwargs == {"force": True}
