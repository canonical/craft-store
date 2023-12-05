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

"""Revisions response models for the Store."""
import datetime
from typing import Any, Dict, List, Optional

from craft_store.models._base_model import MarshableModel
from craft_store.models._charm_model import CharmBaseModel
from craft_store.models._snap_models import Confinement, Grade, Type
from craft_store.models.error_model import ErrorModel


class RevisionsRequestModel(MarshableModel):
    """Resource model for a ReleaseRequestModel.

    :param upload_id: the upload-id returned from the storage endpoint.
    """

    upload_id: str


class RevisionsResponseModel(MarshableModel):
    """Model for a revisions response.

    :param status-url: a URL to monitor the state of the posted revision.
    """

    status_url: str


class RevisionModel(MarshableModel):
    """Base model for all revision types."""

    created_at: datetime.datetime
    revision: int
    sha3_384: str
    status: str

    @classmethod
    def unmarshal(cls, data: Dict[str, Any]) -> "RevisionModel":
        """Unmarshal a revision model."""
        if "bases" in data:
            return CharmRevisionModel.parse_obj(data)
        if "apps" in data:
            return SnapRevisionModel.parse_obj(data)
        if "commit-id" in data:
            return GitRevisionModel.parse_obj(data)
        return RevisionModel.parse_obj(data)


class GitRevisionModel(RevisionModel):
    """A model for a repository commit based revision."""

    commit_id: str
    created_by: str


class CharmRevisionModel(RevisionModel):
    """A revision model for charm revisions."""

    bases: List[CharmBaseModel]
    errors: Optional[List[ErrorModel]] = None
    size: int
    version: str


class SnapRevisionModel(RevisionModel):
    """A model for a snap revision."""

    apps: Optional[List[str]] = None
    architectures: List[str]
    base: Optional[str] = None
    build_url: Optional[str] = None
    confinement: Confinement
    created_by: str
    grade: Grade
    size: int
    type: Type
    version: str
