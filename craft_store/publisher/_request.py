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

from typing import Annotated, Any

import annotated_types
from pydantic import BaseModel, Field
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


class MacaroonRequest(BaseModel):
    """Request for issuing a macaroon."""

    permissions: list[str] = Field(description="List of permissions to grant")
    description: str = Field(description="Description of the macaroon usage")
    ttl: int = Field(description="Time to live in seconds")
    packages: list[dict[str, str]] | None = Field(
        default=None, description="Package restrictions"
    )
    channels: list[str] | None = Field(default=None, description="Channel restrictions")


class ExchangeMacaroonRequest(BaseModel):
    """Request for exchanging macaroons."""

    macaroon: str = Field(description="Discharged macaroon to exchange")


class ExchangeDashboardMacaroonsRequest(BaseModel):
    """Request for exchanging dashboard SSO macaroons."""

    client_description: str | None = Field(
        alias="client-description",
        default=None,
        description="Description of the client",
        max_length=1024,
    )


class OfflineExchangeMacaroonRequest(BaseModel):
    """Request for offline macaroon exchange."""

    macaroon: str = Field(description="The macaroon to exchange offline")


class RevokeMacaroonRequest(BaseModel):
    """Request for revoking a macaroon."""

    session_id: str = Field(description="Session ID of the macaroon to revoke")


class PackageLinks(BaseModel):
    """Links structure for package metadata."""

    contact: list[str] | None = Field(
        default=None, description="Contact URLs", max_length=5
    )
    docs: list[str] | None = Field(
        default=None, description="Documentation URLs", max_length=5
    )
    donations: list[str] | None = Field(
        default=None, description="Donation URLs", max_length=5
    )
    issues: list[str] | None = Field(
        default=None, description="Issues tracker URLs", max_length=5
    )
    source: list[str] | None = Field(
        default=None, description="Source repository URLs", max_length=5
    )
    website: list[str] | None = Field(
        default=None, description="Website URLs", max_length=5
    )


class UpdatePackageMetadataRequest(BaseModel):
    """Request for updating package metadata."""

    contact: str | None = Field(
        default=None, description="Contact information (legacy)"
    )
    default_track: str | None = Field(default=None, description="Default track name")
    description: str | None = Field(default=None, description="Package description")
    links: PackageLinks | None = Field(default=None, description="Package links")
    private: bool | None = Field(default=None, description="Whether package is private")
    summary: str | None = Field(default=None, description="Package summary")
    title: str | None = Field(default=None, description="Package title")
    website: str | None = Field(default=None, description="Project website (legacy)")


class PushResourceRequest(BaseModel):
    """Request for pushing a resource revision."""

    upload_id: str = Field(description="ID of the upload")
    type: str | None = Field(default=None, description="Resource type")
    bases: list[dict[str, Any]] | None = Field(
        default=None, description="Supported bases"
    )


class PushRevisionRequest(BaseModel):
    """Request for pushing/notifying a revision."""

    upload_id: str = Field(description="ID of the upload")
    release: list[dict[str, Any]] | None = Field(
        default=None, description="Release information"
    )


class ResourceRevisionUpdateRequest(BaseModel):
    """Request for updating resource revisions."""

    revision: int = Field(description="Resource revision number")
    bases: list[dict[str, Any]] = Field(description="Supported bases")


class OciImageResourceBlobRequest(BaseModel):
    """Request for OCI image resource blob."""

    image_digest: str = Field(alias="image-digest", description="Image digest")
