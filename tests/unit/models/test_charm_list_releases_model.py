# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
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

import datetime

import pytest
from craft_store.models import charm_list_releases_model


@pytest.fixture
def payload():
    return {
        "channel-map": [
            {
                "base": {"architecture": "amd64", "channel": "20.04", "name": "ubuntu"},
                "channel": "latest/edge",
                "expiration-date": None,
                "progressive": {"paused": None, "percentage": None},
                "resources": [],
                "revision": 5,
                "when": "2021-11-19T11:55:01Z",
            }
        ],
        "package": {
            "channels": [
                {
                    "branch": None,
                    "fallback": None,
                    "name": "latest/stable",
                    "risk": "stable",
                    "track": "latest",
                },
                {
                    "branch": None,
                    "fallback": "latest/stable",
                    "name": "latest/candidate",
                    "risk": "candidate",
                    "track": "latest",
                },
                {
                    "branch": None,
                    "fallback": "latest/candidate",
                    "name": "latest/beta",
                    "risk": "beta",
                    "track": "latest",
                },
                {
                    "branch": None,
                    "fallback": "latest/beta",
                    "name": "latest/edge",
                    "risk": "edge",
                    "track": "latest",
                },
            ]
        },
        "revisions": [
            {
                "bases": [
                    {"architecture": "amd64", "channel": "20.04", "name": "ubuntu"}
                ],
                "created-at": "2021-11-19T11:55:00.084876",
                "errors": None,
                "revision": 5,
                "sha3-384": "849fc881f82f076b4a682ddd902a0a13ddbe1ee01200160f38815b3f537db2b943e12faae4ab74f6aa983a26af19d917",
                "size": 18598,
                "status": "released",
                "version": "5",
            }
        ],
    }


def test_get_list_releases(payload):
    model = charm_list_releases_model.ListReleasesModel(**payload)

    assert len(model.channel_map) == 1
    assert model.channel_map[0].base.architecture == "amd64"
    assert model.channel_map[0].base.channel == "20.04"
    assert model.channel_map[0].base.name == "ubuntu"
    assert model.channel_map[0].channel == "latest/edge"
    assert model.channel_map[0].expiration_date is None
    assert model.channel_map[0].progressive.paused is None
    assert model.channel_map[0].progressive.percentage is None
    assert model.channel_map[0].resources == []
    assert model.channel_map[0].revision == 5
    assert model.channel_map[0].when == datetime.datetime(
        2021, 11, 19, 11, 55, 1, tzinfo=datetime.timezone.utc
    )

    assert len(model.package.channels) == 4
    assert model.package.channels[0].branch is None
    assert model.package.channels[0].fallback is None
    assert model.package.channels[0].name == "latest/stable"
    assert model.package.channels[0].risk == "stable"
    assert model.package.channels[0].track == "latest"
    assert model.package.channels[1].branch is None
    assert model.package.channels[1].fallback == "latest/stable"
    assert model.package.channels[1].name == "latest/candidate"
    assert model.package.channels[1].risk == "candidate"
    assert model.package.channels[1].track == "latest"
    assert model.package.channels[2].branch is None
    assert model.package.channels[2].fallback == "latest/candidate"
    assert model.package.channels[2].name == "latest/beta"
    assert model.package.channels[2].risk == "beta"
    assert model.package.channels[2].track == "latest"
    assert model.package.channels[3].branch is None
    assert model.package.channels[3].fallback == "latest/beta"
    assert model.package.channels[3].name == "latest/edge"
    assert model.package.channels[3].risk == "edge"
    assert model.package.channels[3].track == "latest"

    assert len(model.revisions) == 1
    assert len(model.revisions[0].bases) == 1
    assert model.revisions[0].bases[0].architecture == "amd64"
    assert model.revisions[0].bases[0].channel == "20.04"
    assert model.revisions[0].bases[0].name == "ubuntu"
    # No timezone information returned from Charmhub.
    assert model.revisions[0].created_at == datetime.datetime(
        2021, 11, 19, 11, 55, 0, 84876
    )
    assert model.revisions[0].revision == 5
    assert (
        model.revisions[0].sha3_384
        == "849fc881f82f076b4a682ddd902a0a13ddbe1ee01200160f38815b3f537db2b943e12faae4ab74f6aa983a26af19d917"
    )
    assert model.revisions[0].size == 18598
    assert model.revisions[0].status == "released"
    assert model.revisions[0].version == "5"
