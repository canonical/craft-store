# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
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
"""Tests that only involve reading from the store."""

import pytest
from craft_store import publisher

from tests.integration.conftest import needs_charmhub_credentials


@needs_charmhub_credentials()
@pytest.mark.slow
def test_get_package_metadata(
    publisher_gateway: publisher.PublisherGateway, charmhub_charm_name: str
):
    metadata = publisher_gateway.get_package_metadata(charmhub_charm_name)
    assert metadata.name == charmhub_charm_name
    assert metadata.default_track
    assert len(metadata.id) == len("sCPqM62aJhbLUJmpPfFbsxbd2zpR6dcu")
    assert metadata.default_track in {track.name for track in metadata.tracks}


@needs_charmhub_credentials()
@pytest.mark.slow
def test_list_revisions(
    publisher_gateway: publisher.PublisherGateway, charmhub_charm_name: str
):
    revisions = publisher_gateway.list_revisions(charmhub_charm_name)

    assert len({revision.revision for revision in revisions}) == len(revisions), (
        "Multiple revisions returned with the same revision number."
    )


@needs_charmhub_credentials()
@pytest.mark.slow
def test_list_releases(
    publisher_gateway: publisher.PublisherGateway, charmhub_charm_name: str
):
    response = publisher_gateway.list_releases(charmhub_charm_name)

    # We should only ever have one type of revision.
    # There might be no revisions in which case it could be 0.
    assert len({type(rev) for rev in response.revisions}) in (0, 1)

    channel_names = {channel.name for channel in response.package.channels}
    for channel in response.package.channels:
        assert channel.fallback in channel_names | {None}

        channel_parts = channel.name.split("/")
        assert channel.risk in channel_parts
        assert channel.track in channel_parts
        if channel.branch:
            assert channel.branch in channel_parts
