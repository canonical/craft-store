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
"""Single-endpoint write tests (likely with a read query after)."""

import contextlib
import time

import pytest
from craft_store import errors, publisher

from tests.integration.conftest import needs_charmhub_credentials


@pytest.mark.slow
@needs_charmhub_credentials()
@pytest.mark.parametrize("version_pattern", [None, r"\d+"])
@pytest.mark.parametrize("percentages", [None, 50, 0.32])
def test_create_tracks(
    publisher_gateway: publisher.PublisherGateway,
    charmhub_charm_name: str,
    version_pattern,
    percentages,
):
    track_name = str(time.time_ns())

    tracks_created = publisher_gateway.create_tracks(
        charmhub_charm_name,
        {
            "name": track_name,
            "version-pattern": version_pattern,
            "automatic-phasing-percentage": percentages,
        },
    )
    assert tracks_created == 1

    metadata = publisher_gateway.get_package_metadata(charmhub_charm_name)
    if not metadata.tracks:
        raise ValueError("No tracks returned from the store")

    for track in metadata.tracks:
        if track.name != track_name:
            continue
        assert track.version_pattern == version_pattern
        assert track.automatic_phasing_percentage == percentages
        break
    else:
        raise ValueError(f"Track {track_name} created but not returned from the store.")


@pytest.mark.slow
@needs_charmhub_credentials()
def test_create_disallowed_track(
    publisher_gateway: publisher.PublisherGateway, charmhub_charm_name: str
):
    track_name = "disallowed"

    with pytest.raises(errors.CraftStoreError, match="Invalid track name") as exc_info:
        publisher_gateway.create_tracks(
            charmhub_charm_name,
            {"name": track_name},
        )

    assert exc_info.value.store_errors is not None
    assert "invalid-tracks" in exc_info.value.store_errors


@pytest.mark.slow
@needs_charmhub_credentials()
def test_create_existing_track(
    publisher_gateway: publisher.PublisherGateway, charmhub_charm_name: str
):
    track_name = "1"

    # Suppress the error because we don't care about the first time
    with contextlib.suppress(errors.CraftStoreError):
        publisher_gateway.create_tracks(
            charmhub_charm_name,
            {"name": track_name},
        )

    with pytest.raises(
        errors.CraftStoreError, match="Conflicting track exists"
    ) as exc_info:
        publisher_gateway.create_tracks(
            charmhub_charm_name,
            {"name": track_name},
        )

    assert exc_info.value.store_errors is not None
    assert "conflicting-tracks" in exc_info.value.store_errors
