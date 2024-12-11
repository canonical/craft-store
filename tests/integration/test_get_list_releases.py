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
from typing import cast

import pytest
from craft_store.models import charm_list_releases_model

from .conftest import needs_charmhub_credentials

pytestmark = pytest.mark.timeout(10)  # Timeout if any test takes over 10 sec.


@needs_charmhub_credentials()
@pytest.mark.slow
def test_charm_get_list_releases(charm_client, charmhub_charm_name):
    """Test list releases for a given charm.

    If you need to create this for yourself you can replicate the
    Charmcraft "resources" spread test:
    https://github.com/canonical/charmcraft/blob/main/tests/spread/store/resources/task.yaml
    but with only the Docker image, not the example file.

    Only upload a single revision, and release that to the edge channel.

    Set the charm name to something not already registered in the staging store.
    Set the environment variable CRAFT_STORE_TEST_CHARM to the name of the
    charm you registered before running this test. This will ensure that the
    test will run against your charm.
    """
    model = cast(
        charm_list_releases_model.ListReleasesModel,
        charm_client.get_list_releases(name=charmhub_charm_name),
    )

    assert len(model.channel_map) == 1
    assert model.channel_map[0].base.architecture == "amd64"
    assert model.channel_map[0].base.channel == "22.04"
    assert model.channel_map[0].base.name == "ubuntu"
    assert model.channel_map[0].channel == "latest/edge"
    assert model.channel_map[0].expiration_date is None
    assert model.channel_map[0].progressive.paused is None
    assert model.channel_map[0].progressive.percentage is None
    assert model.channel_map[0].resources == [
        charm_list_releases_model.ResourceModel(
            name="example-image", revision=1, type="oci-image"
        )
    ]
    assert model.channel_map[0].revision == 1
    # Greater than or equal to in order to allow someone to replicate this
    # integration test themselves.
    assert model.channel_map[0].when >= datetime.datetime(
        2023, 4, 13, 16, 12, 55, tzinfo=datetime.timezone.utc
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
    # Greater than or equal to in order to allow someone to replicate this
    # integration test themselves.
    assert model.revisions[0].created_at >= datetime.datetime(
        2023, 4, 13, 16, 9, 55, 19472
    )
    assert model.revisions[0].revision == 1
    assert (
        model.revisions[0].sha3_384
        == "9c1368ba01e30aff43c3372ed61b7cdfc3330b3a3044d887964ccd8100fe2ea59f13409a70596107f981bd09cc9d9b21"
    )
    assert model.revisions[0].size == 6119029
    assert model.revisions[0].status == "released"
    assert model.revisions[0].version == "1"
