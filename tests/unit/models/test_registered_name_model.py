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
"""Tests for RegisteredNameModel."""

import pydantic
import pytest
from craft_store.models import (
    AccountModel,
    RegisteredNameModel,
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
    "links": {"Ubuntu": "https://ubuntu.com/"},
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
    "website": "https://canonical.com/",
}


@pytest.mark.parametrize(
    "json_dict",
    [
        pytest.param(BASIC_REGISTERED_NAME, id="basic"),
        pytest.param(REGISTERED_NAME_ALL_FIELDS, id="all_fields"),
    ],
)
def test_unmarshal(check, json_dict):
    actual = RegisteredNameModel.unmarshal(json_dict)

    check.equal(actual.authority, json_dict.get("authority"))
    check.equal(actual.contact, json_dict.get("contact"))
    check.equal(actual.default_track, json_dict.get("default-track"))
    check.equal(actual.description, json_dict.get("description"))
    check.equal(actual.id, json_dict.get("id"))
    check.equal(actual.links, json_dict.get("links", {}))
    check.equal(
        actual.media, [MediaModel.unmarshal(m) for m in json_dict.get("media", [])]
    )
    check.equal(actual.name, json_dict.get("name"))
    check.equal(actual.private, json_dict["private"] == "true")
    check.equal(actual.publisher, AccountModel.unmarshal(json_dict["publisher"]))
    check.equal(actual.status, json_dict.get("status"))
    check.equal(actual.store, json_dict.get("store"))
    check.equal(actual.summary, json_dict.get("summary"))
    check.equal(actual.title, json_dict.get("title"))
    check.equal(
        actual.tracks, [TrackModel.unmarshal(t) for t in json_dict.get("tracks", [])]
    )
    check.equal(actual.type, json_dict.get("type"))
    if actual.website is None:
        check.is_none(json_dict.get("website"))
    else:
        check.equal(
            actual.website, pydantic.networks.AnyHttpUrl(json_dict.get("website"))
        )
    check.equal(
        actual.track_guardrails,
        [
            TrackGuardrailModel.unmarshal(g)
            for g in json_dict.get("track-guardrails", [])
        ],
    )


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(BASIC_REGISTERED_NAME, id="basic"),
        pytest.param(REGISTERED_NAME_ALL_FIELDS, id="all_fields"),
    ],
)
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
        check.equal(actual, expected)
