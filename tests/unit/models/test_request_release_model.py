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

from typing import cast

from craft_store.models import release_request_model


def test_release_model():
    model = release_request_model.ReleaseRequestModel(channel="edge", revision=1)

    assert model.channel == "edge"
    assert model.resources == []
    assert model.revision == 1


def test_release_model_to_close():
    model = release_request_model.ReleaseRequestModel(channel="edge", revision=None)

    assert model.channel == "edge"
    assert model.resources == []
    assert model.revision is None


def test_release_unmarshal_and_marshal():
    payload = {
        "channel": "stable",
        "revision": 2,
        "resources": [
            {
                "name": "resource-name-4",
                "revision": 4,
            },
            {
                "name": "resource-name-10",
                "revision": 10,
            },
        ],
    }

    model = cast(
        release_request_model.ReleaseRequestModel,
        release_request_model.ReleaseRequestModel.unmarshal(payload),
    )

    assert model.channel == "stable"
    assert model.revision == 2

    assert isinstance(model.resources, list)
    assert len(model.resources) == 2
    assert model.resources[0].name == "resource-name-4"
    assert model.resources[0].revision == 4
    assert model.resources[1].name == "resource-name-10"
    assert model.resources[1].revision == 10

    assert model.marshal() == payload
