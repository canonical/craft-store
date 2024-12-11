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
"""Tests for update_resource_revisions."""

import pytest
from craft_store.models.resource_revision_model import (
    CharmResourceRevisionUpdateRequest,
    RequestCharmResourceBase,
)

from .conftest import needs_charmhub_credentials


@needs_charmhub_credentials()
@pytest.mark.slow
def test_charm_update_resource_revisions(charm_client, charmhub_charm_name):
    resource_name = "empty-file"

    revisions = charm_client.list_resource_revisions(charmhub_charm_name, resource_name)
    revision_numbers = [r.revision for r in revisions[-2:]]
    assert len(revision_numbers) == 2, "Needs more resource revisions"

    resource_updates = [
        CharmResourceRevisionUpdateRequest(
            revision=revision_number,
            bases=[
                RequestCharmResourceBase(
                    name="ubuntu",
                    channel="22.04",
                    architectures=["riscv64"],
                )
            ],
        )
        for revision_number in revision_numbers
    ]
    default_updates = [
        CharmResourceRevisionUpdateRequest(
            revision=revision_number,
            bases=[
                RequestCharmResourceBase(
                    name="all", channel="all", architectures=["all"]
                )
            ],
        )
        for revision_number in revision_numbers
    ]

    update_count = charm_client.update_resource_revisions(
        *resource_updates, name=charmhub_charm_name, resource_name="empty-file"
    )
    assert update_count == len(resource_updates)

    # Reset back to the default.
    update_count = charm_client.update_resource_revisions(
        *default_updates, name=charmhub_charm_name, resource_name="empty-file"
    )
    assert update_count == len(default_updates)
