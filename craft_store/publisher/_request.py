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

from typing import Annotated, Literal

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


UpdateRemoteRequest = TypedDict(
    "UpdateRemoteRequest",
    {
        "action": Literal["setup", "remove"],
        "type": Literal["external", "managed"],
        "name": str,
        "package-type": str,
        "package-name": str,
        "domain-name": NotRequired[str],
        "plane-name": NotRequired[str],
        "url": NotRequired[str],
        "access-token": NotRequired[str],
    },
)
"""Dict representing remote update request."""

CommitWorkflowRequest = TypedDict(
    "CommitWorkflowRequest",
    {
        "action": Literal["commit"],
        "package-type": str,
        "package-name": str,
        "domain-name": NotRequired[str],
        "plane-name": NotRequired[str],
        "commit-hash": str,
        "channel": str,
        "origin-name": str,
    },
)
"""Dict representing commit workflow request."""

PromoteWorkflowRequest = TypedDict(
    "PromoteWorkflowRequest",
    {
        "action": Literal["promote"],
        "package-type": str,
        "package-name": str,
        "source-channel": str,
        "domain-name": NotRequired[str],
        "plane-name": NotRequired[str],
    },
)
"""Dict representing a commit workflow request for promote."""

BuildsetCreateRequest = TypedDict(
    "BuildsetCreateRequest",
    {
        "action": Literal["build"],
        "package-type": str,
        "package-name": str,
        "domain-name": NotRequired[str],
        "plane-name": NotRequired[str],
        "channel": str,
    },
)
"""Dict representing buildset trigger request."""

BuildsetsStatusRequest = TypedDict(
    "BuildsetsStatusRequest",
    {
        "package": str,
        "package-id": NotRequired[str],
        "domain-name": NotRequired[str],
        "plane-name": NotRequired[str],
        "channel": NotRequired[str],
        "commit-hash": NotRequired[str],
        "buildset-id": NotRequired[str],
        "status": NotRequired[str],
    },
)
"""Dict representing buildsets query request."""
