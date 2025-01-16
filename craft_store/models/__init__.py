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
from .account_model import AccountModel
from .charm_list_releases_model import ListReleasesModel as CharmListReleasesModel
from .registered_name_model import RegisteredNameModel
from .release_request_model import ReleaseRequestModel, ResourceModel
from .resource_revision_model import (
    ResponseCharmResourceBase,
    CharmResourceRevisionUpdateRequest,
    CharmResourceType,
    RequestCharmResourceBase,
)
from .revisions_model import (
    RevisionModel,
    RevisionsRequestModel,
    RevisionsResponseModel,
)
from .snap_list_releases_model import ListReleasesModel as SnapListReleasesModel
from .track_guardrail_model import TrackGuardrailModel
from .track_model import TrackModel

__all__ = [
    "AccountModel",
    "CharmListReleasesModel",
    "MarshableModel",
    "RegisteredNameModel",
    "ReleaseRequestModel",
    "ResourceModel",
    "ResponseCharmResourceBase",
    "RequestCharmResourceBase",
    "CharmResourceRevisionUpdateRequest",
    "CharmResourceType",
    "RevisionModel",
    "RevisionsRequestModel",
    "RevisionsResponseModel",
    "SnapListReleasesModel",
    "TrackGuardrailModel",
    "TrackModel",
    "charm_list_releases_model",
    "release_request_model",
    "revisions_model",
    "snap_list_releases_model",
]
