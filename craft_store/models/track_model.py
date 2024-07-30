#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*
#
#  Copyright 2023 Canonical Ltd.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License version 3 as published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""Track model for Craft Store packages."""
from datetime import datetime

from craft_store.models._base_model import MarshableModel


class TrackModel(MarshableModel):
    """A track that a package can be published on."""

    automatic_phasing_percentage: int | None = None
    created_at: datetime
    name: str
    version_pattern: str | None = None
