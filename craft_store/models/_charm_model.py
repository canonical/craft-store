# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
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
"""Generic Charm-related models.

These should only be used to import in other model files. External applications
should point to those imports in case the models change.
"""

from craft_store.models._base_model import MarshableModel


class CharmBaseModel(MarshableModel):
    """Base entries for the channel-map entry from the list_releases endpoint."""

    architecture: str
    channel: str
    name: str


class ResourceModel(MarshableModel):
    """Resource entries for the channel-map entry from the list_releases endpoint."""

    name: str
    revision: int | None = None
    type: str
