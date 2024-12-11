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

from ._base_model import MarshableModel
from ._common_list_releases_model import PackageModel, ProgressiveModel
from .revisions_model import SnapRevisionModel as RevisionModel


class ChannelMapModel(MarshableModel):
    """Model for the channel-map results from the list_releases endpoint."""

    architecture: str
    channel: str
    expiration_date: datetime | None = None
    progressive: ProgressiveModel
    revision: int
    when: datetime


class ListReleasesModel(MarshableModel):
    """Model for the list_releases endpoint."""

    channel_map: list[ChannelMapModel]
    package: PackageModel
    revisions: list[RevisionModel]
