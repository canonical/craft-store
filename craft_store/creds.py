# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
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

"""Functions to serialize/deserialize credentials for Candid and Ubuntu One SSO."""

import json
from typing import Literal

import pydantic
from pydantic import BaseModel, Field

from . import errors


class CandidModel(BaseModel):
    """Model for Candid credentials."""

    token_type: Literal["macaroon"] = Field("macaroon", alias="t")
    value: str = Field(..., alias="v")

    def marshal(self) -> str:
        """Serialize this Candid model into a string suitable for storage."""
        return json.dumps(self.dict(by_alias=True))

    @classmethod
    def unmarshal(cls, marshalled_creds: str) -> "CandidModel":
        """Deserialize a Candid model from previously-stored credentials.

        :param marshalled_creds:
            The previously-stored Candid credentials, which can either be in the "new",
            type-based format or in the "old", raw-string one.
        """
        try:
            creds = json.loads(marshalled_creds)
        except json.JSONDecodeError:
            return CandidModel(v=marshalled_creds)  # pyright: ignore

        if "t" in creds:
            return CandidModel(**creds)
        return CandidModel(v=marshalled_creds)  # pyright: ignore


def marshal_candid_credentials(candid_creds: str) -> str:
    """Serialize Candid credentials for storage.

    This function creates a string that contains the desired `candid_creds` but also
    stores their "type", for unmarshalling later with `unmarshal_candid_credentials()`.

    :param candid_creds: The actual Candid credentials.
    :return: A payload string ready to be passed to Auth.set_credentials()
    """
    return CandidModel(v=candid_creds).marshal()  # pyright: ignore


def unmarshal_candid_credentials(marshalled_creds: str) -> str:
    """Deserialize previously stored Candid credentials.

    This function also handles backwards-compatibility by supporting `marshalled_creds`
    from before we stored the `token_type`; it is meant to be called with the
    returned value from Auth.get_credentials().

    :param marshalled_creds: The credentials retrieved from auth storage.
    :return: The actual Candid credentials.
    """
    try:
        return CandidModel.unmarshal(marshalled_creds).value
    except pydantic.ValidationError as err:
        raise errors.CredentialsNotParseable(
            "Expected valid Candid credentials"
        ) from err


class UbuntuOneMacaroons(BaseModel):
    """Model representation of the set of macaroons used in Ubuntu SSO."""

    root: str = Field(..., alias="r")
    discharge: str = Field(..., alias="d")

    def with_discharge(self, discharge: str) -> "UbuntuOneMacaroons":
        """Create a copy of this UbuntuOneMacaroons with a different discharge macaroon."""
        return self.copy(update={"d": discharge})


class UbuntuOneModel(BaseModel):
    """Model for Ubuntu One credentials."""

    token_type: Literal["u1-macaroon"] = Field("u1-macaroon", alias="t")
    value: UbuntuOneMacaroons = Field(..., alias="v")

    def marshal(self) -> str:
        """Serialize this Ubuntu One model into a string suitable for storage."""
        return json.dumps(self.dict(by_alias=True))

    @classmethod
    def unmarshal(cls, marshalled_creds: str) -> "UbuntuOneModel":
        """Deserialize an Ubuntu One model from previously-stored credentials.

        :param marshalled_creds:
            The previously-stored Ubuntu One credentials, which can either be in the "new",
            type-based format or in the "old", dict-based one.
        """
        creds = json.loads(marshalled_creds)

        if "t" in creds:
            return UbuntuOneModel(**creds)
        return UbuntuOneModel(v=creds)  # pyright: ignore


def marshal_u1_credentials(u1_creds: UbuntuOneMacaroons) -> str:
    """Serialize Ubuntu One credentials for storage.

    This function creates a string that contains the desired `u1_creds` but also
    stores their "type", for unmarshalling later with `unmarshal_u1_credentials()`.

    :param u1_creds: The actual Ubuntu One macaroons credentials.
    :return: A payload string ready to be passed to Auth.set_credentials()
    """
    return UbuntuOneModel(v=u1_creds).marshal()  # pyright: ignore


def unmarshal_u1_credentials(marshalled_creds: str) -> UbuntuOneMacaroons:
    """Deserialize previously stored Ubuntu One credentials.

    This function also handles backwards-compatibility by supporting `marshalled_creds`
    from before we stored the `token_type`; it is meant to be called with the
    returned value from Auth.get_credentials().

    :param marshalled_creds: The credentials retrieved from auth storage.
    :return: The actual Ubuntu One macaroons.
    """
    try:
        return UbuntuOneModel.unmarshal(marshalled_creds).value
    except (json.JSONDecodeError, pydantic.ValidationError) as err:
        raise errors.CredentialsNotParseable(
            "Expected valid Ubuntu One credentials"
        ) from err
