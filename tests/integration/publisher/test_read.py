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
