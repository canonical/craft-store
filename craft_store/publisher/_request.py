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

from collections.abc import Sequence
from enum import Enum
from typing import Annotated

import annotated_types
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict


class PackageType(str, Enum):
    """Enumeration of valid package types."""

    BIN = "bin"
    BUNDLE = "bundle"
    CHARM = "charm"
    ROCK = "rock"
    ROCKCRAFT = "rockcraft"
    SNAP = "snap"
    SNAPCRAFT = "snapcraft"
    SOURCECRAFT = "sourcecraft"
    CHARMCRAFT = "charmcraft"


class IdPackage(TypedDict):
    """Package identified by ID."""

    id: str
    type: PackageType


class NamePackage(TypedDict):
    """Package identified by name."""

    name: str
    type: PackageType


PackageDict = IdPackage | NamePackage


class BaseDict(TypedDict):
    """Base structure for resource bases."""

    name: str
    channel: str
    architectures: Annotated[list[str], annotated_types.MinLen(1)]


class ResourceType(str, Enum):
    """Enumeration of valid resource types."""

    FILE = "file"
    OCI_IMAGE = "oci-image"
    COMPONENT_TEST = "component/test"
    COMPONENT_KERNEL_MODULES = "component/kernel-modules"
    COMPONENT_STANDARD = "component/standard"


class Permission(str, Enum):
    """Enumeration of valid permissions for macaroons."""

    ACCOUNT_MANAGE_KEYS = "account-manage-keys"
    ACCOUNT_MANAGE_METADATA = "account-manage-metadata"
    ACCOUNT_REGISTER_PACKAGE = "account-register-package"
    ACCOUNT_VIEW_PACKAGES = "account-view-packages"
    PACKAGE_MANAGE = "package-manage"
    PACKAGE_MANAGE_ACL = "package-manage-acl"
    PACKAGE_MANAGE_METADATA = "package-manage-metadata"
    PACKAGE_MANAGE_RELEASES = "package-manage-releases"
    PACKAGE_MANAGE_REVISIONS = "package-manage-revisions"
    PACKAGE_VIEW = "package-view"
    PACKAGE_VIEW_ACL = "package-view-acl"
    PACKAGE_VIEW_METADATA = "package-view-metadata"
    PACKAGE_VIEW_METRICS = "package-view-metrics"
    PACKAGE_VIEW_RELEASES = "package-view-releases"
    PACKAGE_VIEW_REVISIONS = "package-view-revisions"
    STORE_MANAGE = "store-manage"
    STORE_VIEW = "store-view"


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

    permissions: set[Permission] | None = Field(
        default=None, description="Set of permissions to grant"
    )
    description: str | None = Field(
        default=None, description="Description of the macaroon usage"
    )
    ttl: int | None = Field(default=None, description="Time to live in seconds", ge=10)
    packages: set[PackageDict] | None = Field(
        default=None, description="Package restrictions"
    )
    channels: set[str] | None = Field(default=None, description="Channel restrictions")


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

    contact: Sequence[Annotated[str, annotated_types.MaxLen(2000)]] | None = Field(
        default=None, description="Contact URLs", max_length=5
    )
    docs: Sequence[Annotated[str, annotated_types.MaxLen(2000)]] | None = Field(
        default=None, description="Documentation URLs", max_length=5
    )
    donations: Sequence[Annotated[str, annotated_types.MaxLen(2000)]] | None = Field(
        default=None, description="Donation URLs", max_length=5
    )
    issues: Sequence[Annotated[str, annotated_types.MaxLen(2000)]] | None = Field(
        default=None, description="Issues tracker URLs", max_length=5
    )
    source: Sequence[Annotated[str, annotated_types.MaxLen(2000)]] | None = Field(
        default=None, description="Source repository URLs", max_length=5
    )
    website: Sequence[Annotated[str, annotated_types.MaxLen(2000)]] | None = Field(
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
    type: ResourceType | None = Field(default=None, description="Resource type")
    bases: Sequence[BaseDict] | None = Field(
        default=None, description="Supported bases"
    )


class PushRevisionRequest(BaseModel):
    """Request for pushing/notifying a revision."""

    upload_id: str = Field(description="ID of the upload")


class ResourceRevisionUpdateRequest(BaseModel):
    """Request for updating resource revisions."""

    revision: int = Field(description="Resource revision number")
    bases: Sequence[BaseDict] = Field(description="Supported bases")


class OciImageResourceBlobRequest(BaseModel):
    """Request for OCI image resource blob."""

    image_digest: str = Field(alias="image-digest", description="Image digest")
