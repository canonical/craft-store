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

"""List Releases Models for Snap Store responses."""


from datetime import datetime
from enum import Enum
from typing import List, Optional

from ._base_model import MarshableModel
from ._common_list_releases_model import PackageModel, ProgressiveModel


class ChannelMapModel(MarshableModel):
    """Model for the channel-map results from the list_releases endpoint."""

    architecture: str
    channel: str
    expiration_date: Optional[datetime]
    progressive: ProgressiveModel
    revision: int
    when: datetime


class Confinement(str, Enum):
    """Snap confinement."""

    CLASSIC = "classic"
    STRICT = "strict"
    DEVMODE = "devmode"


class Grade(str, Enum):
    """Snap grade."""

    DEVEL = "devel"
    STABLE = "stable"


class Type(str, Enum):
    """Type of snap."""

    APP = "app"
    GADGET = "gadget"
    KERNEL = "kernel"
    BASE = "base"
    SNAPD = "snapd"


class RevisionModel(MarshableModel):
    """Model for a revision entry from list_releases."""

    architectures: List[str]
    base: str
    build_url: Optional[str]
    confinement: Confinement
    created_at: datetime
    created_by: str
    grade: Grade
    revision: int
    sha3_384: str
    size: int
    status: str
    type: Type
    version: str


class ListReleasesModel(MarshableModel):
    """Model for the list_releases endpoint."""

    channel_map: List[ChannelMapModel]
    package: PackageModel
    revisions: List[RevisionModel]
