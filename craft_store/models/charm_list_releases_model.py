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

"""List Releases Models for Charmhub responses."""

from datetime import datetime
from typing import Any

from ._base_model import MarshableModel
from ._charm_model import CharmBaseModel, ResourceModel
from ._common_list_releases_model import PackageModel, ProgressiveModel


class ChannelMapModel(MarshableModel):
    """Model for the channel-map results from the list_releases endpoint."""

    base: CharmBaseModel
    channel: str
    expiration_date: datetime | None = None
    progressive: ProgressiveModel
    resources: list[ResourceModel]
    revision: int
    when: datetime


class RevisionModel(MarshableModel):
    """Model for a revision entry from list_releases."""

    bases: list[CharmBaseModel]
    created_at: datetime
    errors: Any = None
    revision: int
    sha3_384: str
    size: int
    status: str
    version: str


class ListReleasesModel(MarshableModel):
    """Model for the list_releases endpoint."""

    channel_map: list[ChannelMapModel]
    package: PackageModel
    revisions: list[RevisionModel]
