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
"""Tests for TrackGuardrailModel"""

import re
from datetime import datetime, timezone

import pytest
from craft_store.models.track_guardrail_model import TrackGuardrailModel

GUARDRAIL_DICT = {"created-at": "2023-03-28T18:50:44+00:00", "pattern": r"^\d\.\d/"}


@pytest.mark.parametrize(
    ("json_dict", "expected"),
    [
        pytest.param(
            GUARDRAIL_DICT,
            TrackGuardrailModel(
                pattern=re.compile(r"^\d\.\d/"),
                **{
                    "created-at": datetime(
                        2023, 3, 28, 18, 50, 44, tzinfo=timezone.utc
                    ),
                },
            ),
        ),
    ],
)
def test_unmarshal(json_dict, expected):
    actual = TrackGuardrailModel.unmarshal(json_dict)

    assert actual == expected


@pytest.mark.parametrize("payload", [GUARDRAIL_DICT])
def test_unmarshal_and_marshal(payload, check):
    marshalled = TrackGuardrailModel.unmarshal(payload).marshal()

    check.equal(payload["pattern"], marshalled["pattern"])
    check.equal(payload["created-at"], marshalled["created-at"])
