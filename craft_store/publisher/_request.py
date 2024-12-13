# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
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
"""Request models for the publisher gateway."""

import re
from typing import Annotated

import pydantic

from craft_store.models import MarshableModel

TRACK_NAME_REGEX = re.compile(r"^[a-zA-Z0-9](?:[_.-]?[a-zA-Z0-9])*$")
"""A regular expression guarding track names.

Retrieved from https://api.staging.charmhub.io/docs/default.html#create_tracks
"""


class CreateTrackRequest(MarshableModel):
    """Model for each track to be created when creating a track."""

    name: Annotated[
        str, pydantic.Field(min_length=1, max_length=28, pattern=TRACK_NAME_REGEX)
    ]
    version_pattern: str | None = None
    automatic_phasing_percentage: int | None = None
