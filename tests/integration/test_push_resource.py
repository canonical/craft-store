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

import hashlib
import time

import pytest
from craft_store.models.resource_revision_model import (
    CharmResourceRevision,
    CharmResourceType,
    RequestCharmResourceBase,
)

from .conftest import needs_charmhub_credentials


@needs_charmhub_credentials()
@pytest.mark.slow
@pytest.mark.parametrize(
    "bases",
    [
        None,
        [],
        [
            RequestCharmResourceBase(
                name="ubuntu", channel="20.04", architectures=["all"]
            )
        ],
        [
            RequestCharmResourceBase(
                name="ubuntu", channel="22.04", architectures=["all"]
            ),
            RequestCharmResourceBase(
                name="ubuntu", channel="24.04", architectures=["all"]
            ),
        ],
    ],
)
def test_charm_push_resource(tmp_path, charm_client, charmhub_charm_name, bases):
    resource_name = "empty-file"
    path = tmp_path / resource_name
    path.unlink(missing_ok=True)
    path.touch()
    file_upload_id = charm_client.upload_file(filepath=path)
    file_status_url = charm_client.push_resource(
        charmhub_charm_name,
        resource_name,
        upload_id=file_upload_id,
        resource_type=CharmResourceType.FILE,
        bases=bases,
    )

    assert file_status_url.startswith(
        f"/v1/charm/{charmhub_charm_name}/revisions/review"
    )

    timeout = time.monotonic() + 120
    while True:
        file_status = charm_client.request(
            "GET", charm_client._base_url + file_status_url
        ).json()["revisions"][0]
        if file_status["status"] in ("approved", "rejected"):
            break
        if time.monotonic() > timeout:
            raise TimeoutError(
                "Zero-byte file upload was not approved or rejected after 120s",
                file_status,
            )
        time.sleep(2)
    assert file_status["revision"] is not None
    file_revisions = charm_client.list_resource_revisions(
        name=charmhub_charm_name, resource_name=resource_name
    )
    for revision in file_revisions:
        if revision.revision == file_status["revision"]:
            break
    else:
        raise ValueError(
            "Zero-byte file revision from status URL does not appear in revisions."
        )
    assert revision.size == 0
    assert revision.sha3_384 == hashlib.sha3_384(b"").hexdigest()
    assert "all" in revision.bases[0].architectures

    assert len(file_revisions) >= 1
    assert isinstance(file_revisions[-1], CharmResourceRevision)
