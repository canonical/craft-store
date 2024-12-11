#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
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
"""Tests for the store trock model."""

from datetime import datetime

import pytest
from craft_store.models.track_model import TrackModel

BASIC_TRACK = {"created-at": "2023-03-28T18:50:44+00:00", "name": "1.0/stable"}
FULL_TRACK = {
    "automatic-phasing-percentage": "10",
    "created-at": "2023-03-28T18:50:44+00:00",
    "name": "1.0/stable",
    "version-pattern": r"^\d\.\d/",
}


@pytest.mark.parametrize(
    "json_dict",
    [
        pytest.param(BASIC_TRACK, id="basic"),
        pytest.param(FULL_TRACK, id="fully-described"),
    ],
)
def test_unmarshal(check, json_dict):
    actual = TrackModel.unmarshal(json_dict)

    check.equal(actual.name, json_dict["name"])
    check.equal(actual.created_at, datetime.fromisoformat(json_dict["created-at"]))
    pct = json_dict.get("automatic-phasing-percentage")
    if isinstance(pct, str):
        pct = int(pct)
    check.equal(actual.automatic_phasing_percentage, pct)
    check.equal(actual.version_pattern, json_dict.get("version-pattern"))


@pytest.mark.parametrize("payload", [BASIC_TRACK, FULL_TRACK])
def test_unmarshal_and_marshal(payload, check):
    marshalled = TrackModel.unmarshal(payload).marshal()

    check.equal(marshalled["created-at"], payload["created-at"])
    check.equal(marshalled["name"], payload["name"])
    check.equal(
        "automatic-phasing-percentage" in marshalled,
        "automatic-phasing-percentage" in payload,
    )
    if "automatic-phasing-percentage" in payload:
        phasing_percentage = int(payload.get("automatic-phasing-percentage"))
    else:
        phasing_percentage = None
    check.equal(marshalled.get("automatic-phasing-percentage"), phasing_percentage)
    check.equal("version-pattern" in marshalled, "version-pattern" in payload)
    check.equal(marshalled.get("version-pattern"), payload.get("version-pattern"))
