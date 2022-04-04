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
import os
from typing import cast

import pytest

from craft_store import StoreClient, endpoints
from craft_store.models import charm_list_releases_model


@pytest.mark.skipif(
    os.getenv("CRAFT_STORE_CHARMCRAFT_CREDENTIALS") is None,
    reason="CRAFT_STORE_CHARMCRAFT_CREDENTIALS are not set",
)
def test_charm_get_list_releases():
    client = StoreClient(
        application_name="integration-test",
        base_url="https://api.charmhub.io",
        storage_base_url="https://storage.charmhub.io",
        endpoints=endpoints.CHARMHUB,
        user_agent="integration-tests",
        environment_auth="CRAFT_STORE_CHARMCRAFT_CREDENTIALS",
    )

    model = cast(
        charm_list_releases_model.ListReleasesModel,
        client.get_list_releases(name="craft-store-test-charm"),
    )

    assert len(model.channel_map) == 1
    assert model.channel_map[0].base.architecture == "amd64"
    assert model.channel_map[0].base.channel == "22.04"
    assert model.channel_map[0].base.name == "ubuntu"
    assert model.channel_map[0].channel == "latest/edge"
    assert model.channel_map[0].expiration_date is None
    assert model.channel_map[0].progressive.paused is None
    assert model.channel_map[0].progressive.percentage is None
    assert model.channel_map[0].resources == []
    assert model.channel_map[0].revision == 1
    assert model.channel_map[0].when == datetime.datetime(
        2022, 4, 3, 22, 28, 21, tzinfo=datetime.timezone.utc
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
    assert model.revisions[0].bases[0].channel == "22.04"
    assert model.revisions[0].bases[0].name == "ubuntu"
    # No timezone information returned from Charmhub.
    assert model.revisions[0].created_at == datetime.datetime(
        2022, 4, 3, 22, 28, 14, 881711
    )
    assert model.revisions[0].revision == 1
    assert (
        model.revisions[0].sha3_384
        == "ba049497f40cadd353dbbbb40a8337b25b76ef1f648af0798c3fcd0dd25e2b1d52aa6795003dc8aef678146ed1a3f49a"
    )
    assert model.revisions[0].size == 6488544
    assert model.revisions[0].status == "released"
    assert model.revisions[0].version == "1"
