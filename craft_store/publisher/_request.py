# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
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
"""Request models for the publisher gateway."""

from typing import Annotated

import annotated_types
from typing_extensions import NotRequired, TypedDict

CreateTrackRequest = TypedDict(
    "CreateTrackRequest",
    {
        "name": Annotated[str, annotated_types.Len(1, 28)],
        "version-pattern": NotRequired[str | None],
        "automatic-phasing-percentage": NotRequired[str | None],
    },
)


class ResourceReleaseRequest(TypedDict):
    """A resource dictionary for a release request."""

    name: str
    """The resource name."""
    revision: NotRequired[int | None]
    """The resource's revision number."""


class ReleaseRequest(TypedDict):
    """Request item for a release."""

    channel: str
    """The channel to release to."""
    resources: NotRequired[list[ResourceReleaseRequest]]
    """A list of resources to attach to this release."""
    revision: int | None
    """The revision to release to the channel."""
