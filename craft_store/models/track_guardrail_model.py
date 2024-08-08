#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*
#
#  Copyright 2023-2024 Canonical Ltd.
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
"""Track guardrails for craft store packages."""

import re
from datetime import datetime
from typing import Annotated

import pydantic

from craft_store.models._base_model import MarshableModel


class TrackGuardrailModel(MarshableModel):
    """A guardrail regular expression for tracks that can be created."""

    pattern: re.Pattern[str]
    created_at: Annotated[  # Prevents pydantic from setting UTC as "...Z"
        datetime,
        pydantic.WrapSerializer(
            lambda dt, _: dt.isoformat(), when_used="json-unless-none"
        ),
    ]
