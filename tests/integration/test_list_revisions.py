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

import pytest
from craft_store.models import revisions_model
from craft_store.models._charm_model import CharmBaseModel

from .conftest import needs_charmhub_credentials


@needs_charmhub_credentials()
@pytest.mark.slow
def test_charm_list_revisions(charm_client, charmhub_charm_name):
    revisions = charm_client.list_revisions(charmhub_charm_name)

    assert len(revisions) >= 1
    assert isinstance(revisions[-1], revisions_model.CharmRevisionModel)

    revision = cast(revisions_model.CharmRevisionModel, revisions[0])

    # Greater than or equal to in order to allow someone to replicate this
    # integration test themselves.
    assert revision.created_at >= datetime.datetime(
        2023, 4, 13, 16, 12, 55, tzinfo=datetime.timezone.utc
    )
    assert revision.size >= 400
    assert len(revision.sha3_384) == 96
    assert set(revision.sha3_384).issubset("0123456789abcdef")
    expected = revisions_model.CharmRevisionModel(
        created_at=revision.created_at,  # For replication purposes
        revision=1,
        sha3_384=revision.sha3_384,
        size=revision.size,
        status="released",
        bases=[CharmBaseModel(name="ubuntu", channel="22.04", architecture="amd64")],
        version="1",
    )
    assert revision == expected
