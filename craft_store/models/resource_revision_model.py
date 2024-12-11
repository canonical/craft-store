# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023-2024 Canonical Ltd.
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
"""Resource revision models for the Store."""

import collections
import datetime
from enum import Enum
from typing import Annotated, TypeVar

import pydantic

from craft_store.models._base_model import MarshableModel

T = TypeVar("T")


def _validate_list_is_unique(value: list[T]) -> list[T]:
    value_set = set(value)
    if len(value_set) == len(value):
        return value
    dupes = [item for item, count in collections.Counter(value).items() if count > 1]
    raise ValueError(f"Duplicate values in list: {dupes}")


UniqueList = Annotated[
    list[T],
    pydantic.AfterValidator(_validate_list_is_unique),
    pydantic.Field(json_schema_extra={"uniqueItems": True}),
]


class CharmResourceType(str, Enum):
    """Resource types for OCI images."""

    OCI_IMAGE = "oci-image"
    FILE = "file"


class ResponseCharmResourceBase(MarshableModel):
    """A base for a charm resource."""

    name: str = "all"
    channel: str = "all"
    architectures: list[str] = ["all"]


class CharmResourceRevision(MarshableModel):
    """A basic resource revision."""

    bases: list[ResponseCharmResourceBase]
    created_at: datetime.datetime
    name: str
    revision: int
    sha256: str
    sha3_384: str
    sha384: str
    sha512: str
    size: pydantic.ByteSize
    type: CharmResourceType | str
    updated_at: datetime.datetime | None = None
    updated_by: str | None = None


class RequestCharmResourceBase(MarshableModel):
    """A base for a charm resource for use in requests."""

    name: str = "all"
    channel: str = "all"
    architectures: UniqueList[str] = pydantic.Field(
        default_factory=lambda: ["all"], min_length=1
    )


RequestCharmResourceBaseList = Annotated[
    list[RequestCharmResourceBase], pydantic.Field(min_length=1)
]


class CharmResourceRevisionUpdateRequest(MarshableModel):
    """A charm resource revision update request."""

    revision: pydantic.PositiveInt
    bases: RequestCharmResourceBaseList
