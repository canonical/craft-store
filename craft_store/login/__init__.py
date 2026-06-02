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

"""Login clients."""

from collections.abc import Collection

import pymacaroons  # type: ignore[import-untyped]

from craft_store.errors import UbuntuOneCredentialsError, UbuntuOneOtpRequiredError

from ._ubuntuone import UbuntuOneLogin


def login_with(
    email: str,
    password: str,
    *,
    api_base_url: str | None = None,
    login_url: str | None = None,
    otp: str | None = None,
    permissions: Collection[str] | None = None,
    channels: Collection[str] | None = None,
    packages: Collection[str] | None = None,
    ttl: int | None = None,
) -> tuple[pymacaroons.Macaroon, pymacaroons.Macaroon]:
    """Login with Ubuntu One credentials and return root and discharged macaroons.

    This is a convenience function that creates an :class:`UbuntuOneLogin` instance
    and calls its :meth:`~UbuntuOneLogin.login_with` method.

    Args:
        email: Ubuntu One email address.
        password: Ubuntu One password.
        api_base_url: The base URL for the store API (e.g., Charmhub, Snapcraft).
            Defaults to the value of the ``CRAFT_STORE_CHARMHUB`` environment variable
            or ``https://api.charmhub.io``.
        login_url: The base URL for Ubuntu One login. Defaults to the value of the
            ``CRAFT_LOGIN_URL`` environment variable or ``https://login.ubuntu.com``.
        otp: Optional one-time password for two-factor authentication.
        permissions: List of permission strings to request (e.g., ``["package-view"]``).
        channels: Optional list of channel names to restrict access to.
        packages: Optional list of package specs to restrict access to.
        ttl: Time-to-live in seconds for the macaroon. Defaults to 86400 (24 hours).

    Returns:
        A tuple of (root_macaroon, discharged_macaroon) ready for use with the store API.
    """
    return UbuntuOneLogin(api_base_url=api_base_url, login_url=login_url).login_with(
        email=email,
        password=password,
        otp=otp,
        permissions=permissions,
        channels=channels,
        packages=packages,
        ttl=ttl,
    )


__all__ = [
    "UbuntuOneCredentialsError",
    "UbuntuOneLogin",
    "UbuntuOneOtpRequiredError",
    "login_with",
]
