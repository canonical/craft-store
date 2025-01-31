# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2025 Canonical Ltd.
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
"""Response models for the publisher gateway."""

import datetime
import enum
from typing import Annotated, Any

import annotated_types
import pydantic

from craft_store.models import _base_model
from craft_store.models._charm_model import CharmBaseModel as Base
from craft_store.models._charm_model import ResourceModel as Resource
from craft_store.models._common_list_releases_model import PackageModel as Package
from craft_store.models._common_list_releases_model import (
    ProgressiveModel as Progressive,
)
from craft_store.models.error_model import ErrorModel as Error

Length = Annotated[int, annotated_types.Ge(0)]
"""An integer that represents the length of an object (non-negative)."""


RevisionNumber = Annotated[int, annotated_types.Ge(1)]
"""A store revision number."""


Sha3_384 = Annotated[
    str, annotated_types.Len(96, 96), pydantic.Field(pattern=r"[0-9a-fA-F]{96}")
]
"""A hexadecimal string containing a sha3-384 digest."""


class SnapConfinement(enum.Enum):
    """Confinement mode for a snap."""

    STRICT = "strict"
    CLASSIC = "classic"
    DEVMODE = "devmode"


class Grade(enum.Enum):
    """Stability grade of a revision."""

    STABLE = "stable"
    DEVEL = "devel"


class SnapType(enum.Enum):
    """The type of a snap."""

    APP = "app"
    OS = "os"
    GADGET = "gadget"
    KERNEL = "kernel"
    BASE = "base"
    SNAPD = "snapd"


class ChannelMap(_base_model.MarshableModel):
    base: Base | None = pydantic.Field(
        description=("The base this revision works on, if relevant in this namespace.")
    )
    channel: str = pydantic.Field(
        description='The channel name, including "latest" for the latest track.',
        examples=["latest/stable", "8/candidate"],
    )
    expiration_date: datetime.datetime | None = pydantic.Field(
        default=None,
        description="When this release expires. If None, the release does not expire.",
    )
    progressive: Progressive | None = pydantic.Field(
        default=None, description="Progressive release state, if relevant."
    )
    resources: list[Resource] | None = pydantic.Field(
        default=None,
        description="The resources attached to this release, if it has any.",
    )
    revision: RevisionNumber
    when: datetime.datetime = pydantic.Field(description="When this release was made.")


class Revision(_base_model.MarshableModel):
    """A flexible model to handle several types of store revisions."""

    created_at: datetime.datetime = pydantic.Field(
        description="When this revision was uploaded.",
    )
    created_by: str | None = pydantic.Field(
        default=None,
        description="The user ID of the account that uploaded this revision, if known",
    )
    errors: list[Error] | None = None
    revision: RevisionNumber
    sha3_384: Sha3_384 | None = None
    size: Length
    status: str
    version: str


class CharmRevision(Revision):
    """A charm-specific revision model."""

    bases: list[Base] | None = pydantic.Field(
        default=None,
        description="The bases this revision supports, if relevant in this namespace.",
    )


class SnapRevision(Revision):
    """A snap-specific revision model."""

    apps: list[str] | None = pydantic.Field(
        default=None,
        description="App commands provided by this revision.",
        examples=[["snapcraft"], ["uv", "uvx"]],
    )
    architectures: list[str] | None = pydantic.Field(
        default=None,
        description="Architectures supported by this revision.",
        examples=[["amd64"], ["riscv64"]],
    )
    base: str | None = pydantic.Field(
        default=None,
        description="The base used by this revision.",
        examples=["bare", "core24"],
    )
    build_url: str | None = None
    confinement: SnapConfinement | None = pydantic.Field(
        default=None,
        description="The confinement used by this revision.",
        examples=[c.value for c in SnapConfinement],
    )
    grade: Grade | None = None
    type_: SnapType | None = pydantic.Field(alias="type", default=None)


class SourceRevision(Revision):
    """A source-specific revision model."""

    commit_id: str | None = None
    craft_yaml: dict[Any, Any] | None = None


class Releases(_base_model.MarshableModel):
    """A model for Releases in the publisher gateway."""

    channel_map: list[ChannelMap]
    package: Package
    revisions: (
        list[Revision] | list[CharmRevision] | list[SnapRevision] | list[SourceRevision]
    )


class ReleasedResourceRevision(_base_model.MarshableModel):
    """A resource revision attached to a release."""

    name: str
    revision: int | None = None


class ReleaseResult(_base_model.MarshableModel):
    """The result of a single release request."""

    channel: str | None = None
    revision: int | None = None
    resources: list[ReleasedResourceRevision] | None = None
