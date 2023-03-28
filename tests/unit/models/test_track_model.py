#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
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
"""Tests for the store trock model."""
from datetime import datetime, timezone

import pytest

from craft_store.models.track_model import TrackModel

BASIC_TRACK = {
    "created-at": "2023-03-28T18:50:44+00:00",
    "name": "1.0/stable"
}
FULL_TRACK = {
    "automatic-phasing-percentage": "10",
    "created-at": "2023-03-28T18:50:44+00:00",
    "name": "1.0/stable",
    "version-pattern": r"^\d\.\d/"
}

@pytest.mark.parametrize(
    "json_dict,expected",
    [
        pytest.param(
            BASIC_TRACK,
            TrackModel(
                name="1.0/stable",
                **{"created-at": datetime(2023, 3, 28, 18, 50, 44, tzinfo=timezone.utc)}
            ),
            id="basic"
        ),
        pytest.param(
            FULL_TRACK,
            TrackModel(
                name="1.0/stable",
                **{
                    "created-at": datetime(2023, 3, 28, 18, 50, 44, tzinfo=timezone.utc),
                    "version-pattern": r"^\d\.\d/",
                    "automatic-phasing-percentage": 10,
                }
            ),
            id="fully-described"
        ),
    ]
)
def test_unmarshal(json_dict, expected):
    actual = TrackModel.unmarshal(json_dict)

    assert actual == expected


@pytest.mark.parametrize("payload", [BASIC_TRACK, FULL_TRACK])
def test_unmarshal_and_marshal(payload, check):
    marshalled = TrackModel.unmarshal(payload).marshal()

    check.equal(marshalled["created-at"].isoformat(), payload["created-at"])
    check.equal(marshalled["name"], payload["name"])
    check.equal(
        "automatic-phasing-percentage" in marshalled,
        "automatic-phasing-percentage" in payload
    )
    if "automatic-phasing-percentage" in payload:
        phasing_percentage = int(payload.get("automatic-phasing-percentage"))
    else:
        phasing_percentage = None
    check.equal(
        marshalled.get("automatic-phasing-percentage"),
        phasing_percentage
    )
    check.equal(
        "version-pattern" in marshalled,
        "version-pattern" in payload
    )
    check.equal(
        marshalled.get("version-pattern"),
        payload.get("version-pattern")
    )

