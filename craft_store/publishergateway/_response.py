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
"""Response models for the publisher gateway."""

from typing import TypedDict

from typing_extensions import NotRequired

PublisherMetadata = TypedDict(
    "PublisherMetadata",
    {
        "display-name": str | None,
        "email": NotRequired[str],
        "id": str,
        "username": str | None,
        "validation": NotRequired[str],
    },
)

TrackMetadata = TypedDict(
    "TrackMetadata",
    {
        "name": str,
        "version-pattern": str | None,
        "automatic-phasing-percentage": float | None,
        "created-at": str,
    },
)


PackageMetadata = TypedDict(
    "PackageMetadata",
    {
        "authority": NotRequired[str | None],
        "contact": NotRequired[str | None],
        "default-track": NotRequired[str | None],
        "description": NotRequired[str | None],
        "id": str,
        "links": NotRequired[list[str] | None],
        "media": list[dict[str, str]],
        "name": NotRequired[str | None],
        "private": bool,
        "publisher": PublisherMetadata,
        "status": str,
        "store": str,
        "summary": NotRequired[str | None],
        "title": NotRequired[str | None],
        "track-guardrails": NotRequired[
            dict[
                str,
                str,
            ]
        ],
        "tracks": list[TrackMetadata] | None,
        "type": str,
        "website": NotRequired[str | None],
    },
)
