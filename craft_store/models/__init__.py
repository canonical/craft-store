#!/usr/bin/env python3
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

"""Models package for store responses."""

from . import (
    charm_list_releases_model,
    release_request_model,
    revisions_model,
    snap_list_releases_model,
)
from ._base_model import MarshableModel
from .charm_list_releases_model import ChannelMapModel as CharmChannelMapModel
from .release_request_model import ReleaseRequestModel
from .revisions_model import RevisionsRequestModel, RevisionsResponseModel
from .snap_list_releases_model import ChannelMapModel as SnapChannelMapModel

__all__ = [
    "CharmChannelMapModel",
    "MarshableModel",
    "ReleaseRequestModel",
    "RevisionsRequestModel",
    "RevisionsResponseModel",
    "SnapChannelMapModel",
    "charm_list_releases_model",
    "release_request_model",
    "revisions_model",
    "snap_list_releases_model",
]
