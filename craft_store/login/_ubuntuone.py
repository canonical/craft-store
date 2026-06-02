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

"""Ubuntu One Login Client."""

import logging
from collections.abc import Collection
from urllib.parse import urljoin, urlparse

import httpx
import pymacaroons  # type: ignore[import-untyped]

from craft_store import auth, creds, errors
from craft_store.creds import DeveloperToken

logger = logging.getLogger(__name__)


class UbuntuOneLogin:
    """A client for handling Ubuntu One authentication with store APIs.

    This class provides methods for logging in with Ubuntu One credentials and obtaining
    macaroon tokens for authenticated access to package stores (Charmhub, Snapcraft, etc.).

    The simplest usage is with the :meth:`login_with` method for a one-step login:

    .. code-block:: python

        root, discharged = UbuntuOneLogin.login_with(
            email="user@example.com",
            password="password123",
            api_base_url="https://api.charmhub.io",
            permissions=["package-view"],
        )

    :param api_base_url: The base URL for the store API (e.g., Charmhub, Snapcraft).
    :param login_url: The base URL for Ubuntu One login. Defaults to
        ``https://login.ubuntu.com``.
    :param application_name: The name of the application using this client.
    :param store_auth: An optional :class:`craft_store.auth.Auth` instance to use.
    """

    def __init__(
        self,
        api_base_url: str,
        *,
        login_url: str | None = None,
        application_name: str = "craft-store-ubuntu-one",
        store_auth: auth.Auth | None = None,
    ) -> None:
        """Create a login client."""
        self._login_url = login_url or "https://login.ubuntu.com"
        self._api_base_url = api_base_url
        self._application_name = application_name
        self._store_auth = store_auth or auth.Auth(
            application_name=application_name,
            host=urlparse(self._api_base_url).netloc,
            ephemeral=False,
            file_fallback=False,
        )

    @classmethod
    def login_with(
        cls,
        email: str,
        password: str,
        *,
        api_base_url: str,
        login_url: str | None = None,
        application_name: str = "craft-store-ubuntu-one",
        store_auth: auth.Auth | None = None,
        otp: str | None = None,
        permissions: Collection[str] | None = None,
        channels: Collection[str] | None = None,
        packages: Collection[str] | None = None,
        ttl: int | None = None,
    ) -> tuple[pymacaroons.Macaroon, pymacaroons.Macaroon]:
        """Login with Ubuntu One credentials and return root and discharged macaroons.

        This is the primary method for authentication. It requests a macaroon from the
        store API and discharges it using your Ubuntu One credentials.

        :param email: Ubuntu One email address.
        :param password: Ubuntu One password.
        :param api_base_url: The base URL for the store API (e.g., Charmhub, Snapcraft).
        :param login_url: The base URL for Ubuntu One login. Defaults to
            ``https://login.ubuntu.com``.
        :param application_name: The name of the application using this client.
        :param store_auth: An optional :class:`craft_store.auth.Auth` instance to use.
        :param otp: Optional one-time password for two-factor authentication.
        :param permissions: List of permission strings to request (e.g.,
            ``["package-view"]``). If not provided, defaults to
            ``["account-view-packages"]``. See store API documentation for valid
            permission values.
        :param channels: Optional list of channel names to restrict access to.
        :param packages: Optional list of package specs to restrict access to.
        :param ttl: Time-to-live in seconds for the macaroon. Defaults to 86400
            (24 hours).

        :return: A tuple of (root_macaroon, discharged_macaroon) ready for use with the
            store API. The header should be formatted as:
            ``Macaroon root={root.serialize()}, discharge={root.prepare_for_request(discharged).serialize()}``

        :raises httpx.HTTPStatusError: If any HTTP request fails.
        :raises ValueError: If the macaroon has invalid caveats.
        :raises craft_store.errors.UbuntuOneOtpRequiredError: If two-factor
            authentication is required but no OTP was provided.
        :raises craft_store.errors.UbuntuOneCredentialsError: If the provided
            credentials are invalid.
        """
        instance = cls(
            api_base_url=api_base_url,
            login_url=login_url,
            application_name=application_name,
            store_auth=store_auth,
        )
        return instance._login(
            email=email,
            password=password,
            otp=otp,
            permissions=permissions,
            channels=channels,
            packages=packages,
            ttl=ttl,
        )

    def _login(
        self,
        email: str,
        password: str,
        *,
        otp: str | None = None,
        permissions: Collection[str] | None = None,
        channels: Collection[str] | None = None,
        packages: Collection[str] | None = None,
        ttl: int | None = None,
    ) -> tuple[pymacaroons.Macaroon, pymacaroons.Macaroon]:
        """Login with Ubuntu One credentials and return root and discharged macaroons."""
        if permissions is None:
            permissions = ["account-view-packages"]

        root = self._get_macaroon(
            permissions=permissions,
            channels=channels,
            packages=packages,
            ttl=ttl,
        )
        try:
            discharged = self._discharge_macaroon(
                root,
                email=email,
                password=password,
                otp=otp,
            )
        except httpx.HTTPStatusError as exc:
            if self._is_otp_required(exc):
                raise errors.UbuntuOneOtpRequiredError from exc
            if exc.response.status_code in {400, 401}:
                raise errors.UbuntuOneCredentialsError from exc
            raise

        self._save_credentials(root, discharged)
        return root, discharged

    def _get_macaroon(
        self,
        *,
        permissions: Collection[str],
        channels: Collection[str] | None = None,
        packages: Collection[str] | None = None,
        ttl: int | None = None,
    ) -> pymacaroons.Macaroon:
        """Request an unsigned macaroon from the store API.

        :param permissions: List of permission strings (e.g., ``["package-view"]``,
            ``["package-manage"]``). Required.
        :param channels: Optional list of channel names to restrict access to.
        :param packages: Optional list of package specs to restrict access to.
        :param ttl: Time-to-live in seconds. Defaults to 86400 (24 hours).

        :return: An unsigned macaroon that must be discharged with
            _discharge_macaroon.

        :raises httpx.HTTPStatusError: If the request to the store API fails.
        """
        if ttl is None:
            ttl = 86400  # 24 hours default

        request_object = {
            "permissions": list(permissions),
            "ttl": ttl,
        }
        if channels is not None:
            request_object["channels"] = list(channels)
        if packages is not None:
            request_object["packages"] = list(packages)

        # Construct the macaroon request endpoint
        macaroon_url = f"{self._api_base_url}/v1/tokens/usso"

        macaroon_response = httpx.post(
            macaroon_url,
            json=request_object,
            timeout=60.0,
        )
        macaroon_response.raise_for_status()
        try:
            macaroon = str(macaroon_response.json()["macaroon"])
        except (TypeError, KeyError) as exc:
            raise errors.InvalidResponseError(
                macaroon_response,
                details="Missing 'macaroon' in /v1/tokens/usso response",
            ) from exc
        return pymacaroons.Macaroon.deserialize(macaroon)

    def _get_login_caveat(
        self, caveats: list[pymacaroons.Caveat]
    ) -> pymacaroons.Caveat:
        match len(caveats):
            case 0:
                raise ValueError("Invalid macaroon: no third-party caveats found")
            case 1:
                return caveats[0]

        login_host = urlparse(self._login_url).netloc

        # Try to find caveat by location matching our login host
        for caveat in caveats:
            if caveat.location and login_host in caveat.location:
                return caveat

        # Fall back to any caveat with a location
        for caveat in caveats:
            if caveat.location:
                return caveat

        return caveats[0]

    def _discharge_macaroon(
        self,
        macaroon: pymacaroons.Macaroon,
        *,
        email: str,
        password: str,
        otp: str | None = None,
    ) -> pymacaroons.Macaroon:
        """Discharge a macaroon using Ubuntu One credentials."""
        login_caveat = self._get_login_caveat(
            macaroon.third_party_caveats(),
        )
        # caveat_id might be bytes, ensure it's a string
        caveat_id = login_caveat.caveat_id
        if isinstance(caveat_id, bytes):
            caveat_id = caveat_id.decode("utf-8")
        else:
            caveat_id = str(caveat_id)

        discharge_request = {
            "email": email,
            "password": password,
            "caveat_id": caveat_id,
        }
        if otp:
            discharge_request["otp"] = otp

        # Use the configured login URL as the base for the discharge request
        discharge_url = urljoin(self._login_url, "api/v2/tokens/discharge")

        # Discharge at the login location
        discharge_response = httpx.post(
            discharge_url,
            json=discharge_request,
            timeout=60.0,
        )
        discharge_response.raise_for_status()
        return pymacaroons.Macaroon.deserialize(
            discharge_response.json()["discharge_macaroon"]
        )

    def _save_credentials(
        self,
        root: pymacaroons.Macaroon,
        discharge: pymacaroons.Macaroon,
    ) -> None:
        credentials = creds.marshal_u1_credentials(
            creds.UbuntuOneMacaroons(r=root.serialize(), d=discharge.serialize())
        )
        logger.debug(
            "Storing Ubuntu One credentials for %r on %r.",
            self._application_name,
            getattr(self._store_auth, "host", "<unknown>"),
        )
        self._store_auth.set_credentials(credentials, force=True)

    @staticmethod
    def _is_otp_required(exc: httpx.HTTPStatusError) -> bool:
        try:
            response_json = exc.response.json()
        except ValueError:
            return False

        error_list = response_json.get("error_list") or response_json.get("error-list")
        if isinstance(error_list, list):
            for error in error_list:
                if not isinstance(error, dict):
                    continue
                code = str(error.get("code", "")).lower()
                message = str(error.get("message", "")).lower()
                if "twofactor-required" in code or "otp required" in message:
                    return True
        message = str(response_json.get("message", "")).lower()
        code = str(response_json.get("code", "")).lower()
        return "twofactor-required" in code or "otp required" in message
