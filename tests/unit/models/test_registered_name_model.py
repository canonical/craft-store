#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*
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
"""Tests for RegisteredNameModel."""
import re
from datetime import datetime, timezone

import pytest

from craft_store.models import (
    RegisteredNameModel,
    AccountModel,
    TrackGuardrailModel,
    TrackModel,
)
from craft_store.models.registered_name_model import MediaModel

BASIC_REGISTERED_NAME = {
    "id": "123",
    "private": "true",
    "publisher": {"id": "456"},
    "status": "registered",
    "store": "ubuntu",
    "type": "charm",
}
REGISTERED_NAME_ALL_FIELDS = {
    "authority": "Mark",
    "contact": "charmcrafters@lists.canonical.com",
    "default-track": "lts",
    "description": "This is a thing",
    "id": "123",
    "links": ["https://ubuntu.com/"],
    "media": [
        {"type": "icon", "url": "https://assets.ubuntu.com/v1/0843d517-favicon.ico"}
    ],
    "name": "charming-charm",
    "private": "false",
    "publisher": {"id": "456"},
    "status": "registered",
    "store": "ubuntu",
    "summary": "This is a thing",
    "title": "Some charming charm",
    "track-guardrails": [
        {"created-at": "2023-03-28T18:50:44+00:00", "pattern": r"^\d\.\d/"}
    ],
    "tracks": [{"created-at": "2023-03-28T18:50:44+00:00", "name": "1.0/stable"}],
    "type": "charm",
    "website": "https://canonical.com",
}


@pytest.mark.parametrize(
    "json_dict,expected",
    [
        pytest.param(
            BASIC_REGISTERED_NAME,
            RegisteredNameModel(
                id="123",
                private=True,
                publisher=AccountModel(id="456"),
                status="registered",
                store="ubuntu",
                media=[],
                tracks=[],
                type="charm",
                **{"track-guardrails": []}
            ),
            id="basic",
        ),
        pytest.param(
            REGISTERED_NAME_ALL_FIELDS,
            RegisteredNameModel(
                authority="Mark",
                contact="charmcrafters@lists.canonical.com",
                description="This is a thing",
                id="123",
                links=["https://ubuntu.com/"],
                media=[
                    MediaModel(
                        type="icon",
                        url="https://assets.ubuntu.com/v1/0843d517-favicon.ico",
                    )
                ],
                name="charming-charm",
                private=False,
                publisher=AccountModel(id="456"),
                status="registered",
                store="ubuntu",
                summary="This is a thing",
                title="Some charming charm",
                tracks=[
                    TrackModel.unmarshal(
                        {
                            "created-at": "2023-03-28T18:50:44+00:00",
                            "name": "1.0/stable",
                        }
                    ),
                ],
                type="charm",
                website="https://canonical.com",
                **{
                    "default-track": "lts",
                    "track-guardrails": [
                        TrackGuardrailModel.unmarshal(
                            {
                                "created-at": "2023-03-28T18:50:44+00:00",
                                "pattern": r"^\d\.\d/",
                            }
                        )
                    ],
                }
            ),
            id="all_fields",
        ),
    ],
)
def test_unmarshal(json_dict, expected):
    actual = RegisteredNameModel.unmarshal(json_dict)

    assert actual == expected


@pytest.mark.parametrize("payload", [BASIC_REGISTERED_NAME, REGISTERED_NAME_ALL_FIELDS])
def test_unmarshal_and_marshal(payload, check):
    marshalled = RegisteredNameModel.unmarshal(payload).marshal()
    not_set = [[["NOT SET"]]]

    check.equal(marshalled.keys(), payload.keys())

    for field in payload:
        actual = marshalled.get(field, not_set)
        expected = payload.get(field, not_set)
        if field == "private":
            expected = payload[field].lower() == "true"
        elif field in ("track-guardrails", "tracks"):
            expected = payload[field].copy()
            for item in expected:
                item["created-at"] = datetime.fromisoformat(item["created-at"])
                if field == "track-guardrails":
                    item["pattern"] = re.compile(item["pattern"])
        check.equal(actual, expected)
