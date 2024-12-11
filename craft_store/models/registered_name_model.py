# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023-2024 Canonical Ltd.
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

"""Registered Names models for the Store."""

from typing import Any, Literal

import pydantic
from pydantic import AnyHttpUrl, Field

from ._base_model import MarshableModel
from .account_model import AccountModel
from .track_guardrail_model import TrackGuardrailModel
from .track_model import TrackModel


class MediaModel(MarshableModel):
    """Resource model for a media item attached to a registered name."""

    type: Literal["icon"]
    url: AnyHttpUrl


class RegisteredNameModel(MarshableModel):
    """Resource model for a registered name."""

    authority: str | None = None
    contact: str | None = None
    default_track: str | None = None
    description: str | None = None
    id: str
    links: dict[str, Any] = Field(default_factory=dict)
    media: list[MediaModel] = Field(default_factory=list)
    name: str | None = None
    private: bool
    publisher: AccountModel
    status: str
    store: str
    summary: str | None = None
    title: str | None = None
    track_guardrails: list[TrackGuardrailModel] = Field(default_factory=list)
    tracks: list[TrackModel] = Field(default_factory=list)
    type: str
    website: AnyHttpUrl | None = None

    @pydantic.field_serializer("website")
    def _serialize_website(self, website: AnyHttpUrl | None) -> str | None:
        if not website:
            return None
        return str(website)
