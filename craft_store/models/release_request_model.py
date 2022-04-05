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

"""Release request models for the Store."""

from typing import List, Optional

from pydantic import Field

from ._base_model import MarshableModel


class ResourceModel(MarshableModel):
    """Resource model for a ReleaseRequestModel.

    :param name: name of the resource to release.
    :param revision: revision of the resource to release.
    """

    name: str
    revision: Optional[int]


class ReleaseRequestModel(MarshableModel):
    """Model to request a release to the store.

    :param channel: name of the channel to release to.
    :param resources: resources to release with this revision.
    :param revision: revision to release.
    """

    channel: str
    resources: Optional[List[ResourceModel]] = Field(default_factory=list)
    revision: Optional[int] = Field(...)
