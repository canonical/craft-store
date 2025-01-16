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


@pytest.mark.slow
@needs_charmhub_credentials()
@pytest.mark.parametrize("entity_type", ["charm", "bundle"])
def test_register_unregister_cycle(
    publisher_gateway: publisher.PublisherGateway,
    entity_type: str,
    unregistered_charm_name: str,
):
    try:
        publisher_gateway.register_name(
            unregistered_charm_name, entity_type=entity_type
        )

        names = {pkg.name for pkg in publisher_gateway.list_registered_names()}
        assert unregistered_charm_name in names, (
            f"{entity_type} was not successfully registered."
        )
    finally:
        publisher_gateway.unregister_name(unregistered_charm_name)

    names = {result.name for result in publisher_gateway.list_registered_names()}
    assert unregistered_charm_name not in names, (
        f"{entity_type} was not successfully unregistered."
    )


@needs_charmhub_credentials()
@pytest.mark.slow
def test_release(
    publisher_gateway: publisher.PublisherGateway, charmhub_charm_name: str
):
    # Find a revision to release.
    releases = publisher_gateway.list_releases(charmhub_charm_name)

    for channel in releases.channel_map:
        if channel.channel != "latest/edge":
            break
    else:
        raise ValueError(
            f"Please release at least one revision of {charmhub_charm_name} to a channel other than latest/edge"
        )

    for revision_to_release in releases.revisions:
        if revision_to_release.revision == channel.revision:
            break
    else:
        raise ValueError(
            f"Cannot find revision to release (revision {channel.revision})"
        )

    # Try releasing that revision to edge.

    results = publisher_gateway.release(
        charmhub_charm_name, [{"channel": "latest/edge", "revision": channel.revision}]
    )
    assert results[0].revision == revision_to_release.revision
    assert results[0].channel in ("latest/edge", "edge")  # Could be either!
