# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
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
"""Tests for list_releases."""
import datetime
from typing import cast

import pydantic
from craft_store.models.resource_revision_model import (
    CharmResourceBase,
    CharmResourceRevision,
    CharmResourceType,
)

from .conftest import needs_charmhub_credentials


@needs_charmhub_credentials()
def test_charm_list_resource_revisions(charm_client, charmhub_charm_name):
    revisions = charm_client.list_resource_revisions(charmhub_charm_name, "empty-file")

    assert len(revisions) >= 1
    assert isinstance(revisions[-1], CharmResourceRevision)

    actual = cast(CharmResourceRevision, revisions[-1])

    # Greater than or equal to in order to allow someone to replicate this
    # integration test themselves.
    assert actual.created_at >= datetime.datetime(
        2023, 12, 1, tzinfo=datetime.timezone.utc
    )
    assert actual.revision >= 1

    expected = CharmResourceRevision(
        name="empty-file",
        bases=[CharmResourceBase()],
        type=CharmResourceType.FILE,
        # These values are for an empty file.
        size=pydantic.ByteSize(0),
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        sha384="38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b",
        sha3_384="0c63a75b845e4f7d01107d852e4c2485c51a50aaaa94fc61995e71bbee983a2ac3713831264adb47fb6bd1e058d5f004",
        sha512="cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
        # Copy the actual revision properties.
        created_at=actual.created_at,
        revision=actual.revision,
        updated_at=actual.updated_at,
        updated_by=actual.updated_by,
    )
    assert actual == expected
