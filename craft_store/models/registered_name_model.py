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

"""Registered Names models for the Store."""
import datetime
import numbers
from typing import Optional, List, Literal, Pattern, Dict, Any

from overrides import override
from pydantic import AnyHttpUrl, Field

from . import AccountModel, TrackGuardrailModel, TrackModel
from ._base_model import MarshableModel


class MediaModel(MarshableModel):
    """Resource model for a media item attached to a registered name."""

    type: Literal["icon"]
    url: AnyHttpUrl


class RegisteredNameModel(MarshableModel):
    """Resource model for a registered name."""

    authority: Optional[str]
    contact: Optional[str]
    default_track: Optional[str]
    description: Optional[str]
    id: str
    links: Dict[str, Any] = Field(default_factory=dict)
    media: List[MediaModel] = Field(default_factory=list)
    name: Optional[str]
    private: bool
    publisher: AccountModel
    status: str
    store: str
    summary: Optional[str]
    title: Optional[str]
    track_guardrails: List[TrackGuardrailModel] = Field(default_factory=list)
    tracks: List[TrackModel] = Field(default_factory=list)
    type: str
    website: Optional[AnyHttpUrl]
