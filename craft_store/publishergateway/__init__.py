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
"""Package containing the Publisher Gateway client and relevant metadata."""

from ._request import (
    CreateTrackRequest,
)

from ._response import (
    PackageMetadata,
    PublisherMetadata,
    TrackMetadata,
)
from ._publishergw import PublisherGateway

__all__ = [
    "CreateTrackRequest",
    "PackageMetadata",
    "PublisherMetadata",
    "TrackMetadata",
    "PublisherGateway",
]
