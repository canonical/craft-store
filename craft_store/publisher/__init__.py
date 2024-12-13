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
from ._publishergw import PublisherGateway

from craft_store.models.account_model import AccountModel as Account
from craft_store.models.registered_name_model import MediaModel as Media
from craft_store.models.registered_name_model import (
    RegisteredNameModel as RegisteredName,
)
from craft_store.models.track_guardrail_model import (
    TrackGuardrailModel as TrackGuardrail,
)
from craft_store.models.track_model import TrackModel as Track

__all__ = [
    "Account",
    "CreateTrackRequest",
    "Media",
    "RegisteredName",
    "TrackGuardrail",
    "Track",
    "PublisherGateway",
]
