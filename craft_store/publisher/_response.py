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
from craft_store.models.resource_revision_model import CharmResourceRevision

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


class MacaroonResponse(_base_model.MarshableModel):
    """Response from macaroon issuance."""

    macaroon: str = pydantic.Field(description="The issued macaroon")
    expires: datetime.datetime | None = pydantic.Field(
        default=None, description="When the macaroon expires"
    )


class ExistingMacaroon(_base_model.MarshableModel):
    """Information about an existing macaroon."""

    description: str | None = pydantic.Field(
        default=None, description="Macaroon description"
    )
    revoked_at: str | None = pydantic.Field(default=None, description="When revoked")
    revoked_by: str | None = pydantic.Field(default=None, description="Who revoked it")
    session_id: str = pydantic.Field(description="Session ID")
    valid_since: datetime.datetime = pydantic.Field(description="Valid from date")
    valid_until: datetime.datetime = pydantic.Field(description="Valid until date")


class GetMacaroonResponse(_base_model.MarshableModel):
    """Response from get_macaroon endpoint."""

    macaroon: str | None = pydantic.Field(
        default=None, description="Bakery v2 macaroon for discharge"
    )
    macaroons: list[ExistingMacaroon] | None = pydantic.Field(
        default=None, description="Existing macaroons"
    )


class MacaroonAccount(_base_model.MarshableModel):
    """Account information from macaroon info."""

    id: str = pydantic.Field(description="Account ID")
    email: str | None = pydantic.Field(default=None, description="Account email")
    username: str | None = pydantic.Field(default=None, description="Account username")
    display_name: str | None = pydantic.Field(
        default=None, description="Account display name"
    )
    validation: str | None = pydantic.Field(
        default=None, description="Account validation status"
    )


class MacaroonPackage(_base_model.MarshableModel):
    """Package information from macaroon info."""

    id: str | None = pydantic.Field(default=None, description="Package ID")
    name: str | None = pydantic.Field(default=None, description="Package name")
    type: str = pydantic.Field(description="Package type (charm, snap, etc.)")


class MacaroonInfo(_base_model.MarshableModel):
    """Information about the authenticated macaroon token."""

    account: MacaroonAccount = pydantic.Field(description="Account information")
    permissions: list[str] | None = pydantic.Field(
        default=None, description="Granted permissions"
    )
    packages: list[MacaroonPackage] | None = pydantic.Field(
        default=None, description="Package restrictions"
    )
    channels: list[str] | None = pydantic.Field(
        default=None, description="Channel restrictions"
    )


class ExchangeMacaroonResponse(_base_model.MarshableModel):
    """Response from macaroon exchange."""

    macaroon: str = pydantic.Field(description="The exchanged macaroon")


class ExchangeDashboardMacaroonsResponse(_base_model.MarshableModel):
    """Response from dashboard macaroon exchange."""

    macaroon: str = pydantic.Field(description="The developer token")


class OfflineExchangeMacaroonResponse(_base_model.MarshableModel):
    """Response from offline macaroon exchange."""

    macaroon: str = pydantic.Field(description="The exchanged offline macaroon")


class RevokeMacaroonResponse(_base_model.MarshableModel):
    """Response from macaroon revocation."""

    macaroons: list[ExistingMacaroon] = pydantic.Field(
        description="Updated list of macaroons after revocation"
    )


class UploadReview(_base_model.MarshableModel):
    """An upload review revision item."""

    upload_id: str = pydantic.Field(description="Upload ID")
    status: str = pydantic.Field(description="Review status")
    revision: int | None = pydantic.Field(description="Revision number if assigned")
    errors: list[Error] | None = pydantic.Field(
        default=None, description="Review errors"
    )


class UploadReviewsList(_base_model.MarshableModel):
    """List of upload review revisions."""

    revisions: list[UploadReview] = pydantic.Field(
        description="List of upload review revisions"
    )


class ResourceInfo(_base_model.MarshableModel):
    """Information about a declared resource."""

    name: str = pydantic.Field(description="Resource name")
    type: str = pydantic.Field(description="Resource type")
    optional: bool | None = pydantic.Field(
        default=None, description="Whether resource is optional"
    )
    revision: int | None = pydantic.Field(default=None, description="Resource revision")


class ResourcesList(_base_model.MarshableModel):
    """List of resources."""

    resources: list[ResourceInfo] = pydantic.Field(description="List of resources")


class ResourceRevisionsList(_base_model.MarshableModel):
    """List of resource revisions."""

    revisions: list[CharmResourceRevision] = pydantic.Field(
        description="List of resource revisions"
    )


class UpdateResourceRevisionsResponse(_base_model.MarshableModel):
    """Response from updating resource revisions."""

    num_resource_revisions_updated: int = pydantic.Field(
        description="Number of resource revisions updated"
    )


class PushResourceResponse(_base_model.MarshableModel):
    """Response from pushing a resource."""

    status_url: str = pydantic.Field(description="URL to check upload status")


class PushRevisionResponse(_base_model.MarshableModel):
    """Response from pushing/notifying a revision."""

    status_url: str = pydantic.Field(description="URL to check upload status")


class OciImageResourceUploadCredentialsResponse(_base_model.MarshableModel):
    """Response from OCI image resource upload credentials."""

    image_name: str = pydantic.Field(alias="image-name", description="Image name")
    username: str = pydantic.Field(description="Registry username")
    password: str = pydantic.Field(description="Registry password")


class OciImageResourceBlobResponse(_base_model.MarshableModel):
    """Response from OCI image resource blob."""

    image_name: str = pydantic.Field(alias="ImageName", description="Image name")
    username: str = pydantic.Field(alias="Username", description="Username")
    password: str = pydantic.Field(alias="Password", description="Password")


class PackageMedia(_base_model.MarshableModel):
    """Media object in package metadata."""

    type: str = pydantic.Field(description="Media type (e.g., 'icon')")
    url: str = pydantic.Field(description="Media URL")


class PackagePublisher(_base_model.MarshableModel):
    """Publisher information in package metadata."""

    id: str = pydantic.Field(description="Publisher ID")
    email: str = pydantic.Field(description="Publisher email")
    username: str | None = pydantic.Field(
        default=None, description="Publisher username"
    )
    display_name: str | None = pydantic.Field(
        default=None, description="Publisher display name"
    )
    validation: str = pydantic.Field(description="Publisher validation status")


class PackageTrackGuardrail(_base_model.MarshableModel):
    """Track guardrail information."""

    pattern: str = pydantic.Field(description="Track pattern")
    created_at: str = pydantic.Field(description="Creation timestamp")


class PackageTrack(_base_model.MarshableModel):
    """Track information."""

    name: str = pydantic.Field(description="Track name")
    version_pattern: str | None = pydantic.Field(
        default=None, description="Version pattern"
    )
    created_at: str = pydantic.Field(description="Creation timestamp")
    automatic_phasing_percentage: float | None = pydantic.Field(
        default=None, description="Automatic phasing percentage"
    )


class PackageMetadata(_base_model.MarshableModel):
    """Complete package metadata."""

    id: str = pydantic.Field(description="Package ID")
    name: str | None = pydantic.Field(default=None, description="Package name")
    title: str | None = pydantic.Field(default=None, description="Package title")
    summary: str | None = pydantic.Field(default=None, description="Package summary")
    description: str | None = pydantic.Field(
        default=None, description="Package description"
    )
    contact: str | None = pydantic.Field(
        default=None, description="Contact information"
    )
    website: str | None = pydantic.Field(default=None, description="Website URL")
    default_track: str | None = pydantic.Field(
        default=None, description="Default track"
    )
    private: bool = pydantic.Field(description="Whether package is private")
    status: str = pydantic.Field(description="Package status")
    store: str = pydantic.Field(description="Store name")
    type: str = pydantic.Field(description="Package type")
    authority: str | None = pydantic.Field(
        default=None, description="Package authority"
    )
    links: dict[str, list[str]] | None = pydantic.Field(
        default=None, description="Package links"
    )
    media: list[PackageMedia] | None = pydantic.Field(
        default=None, description="Package media"
    )
    publisher: PackagePublisher = pydantic.Field(description="Publisher information")
    track_guardrails: list[PackageTrackGuardrail] | None = pydantic.Field(
        default=None, description="Track guardrails"
    )
    tracks: list[PackageTrack] | None = pydantic.Field(
        default=None, description="Package tracks"
    )


class UpdatePackageMetadataResponse(_base_model.MarshableModel):
    """Response from updating package metadata."""

    metadata: PackageMetadata = pydantic.Field(description="Updated package metadata")
