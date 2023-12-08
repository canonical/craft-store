# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021-2022 Canonical Ltd.
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
"""Full workflow tests for charms."""
import time

from craft_store.models import revisions_model

from tests.integration.conftest import needs_charmhub_credentials


@needs_charmhub_credentials()
def test_full_charm_workflow(charm_client, charmhub_charm_name, fake_charms):
    """A workflow test for uploading a full charm.

    Steps include:
    1. Check if charm name is registered.
       1.1. Register if necessary.
    2. Upload one or more charm revisions
    Once we implement https://github.com/canonical/craft-store/issues/124:
    3. Upload one or more OCI images (must already exist on disk)
    4. Upload a fresh file
    5. Upload an empty file
    6. Modify the bases for a resource.
    """
    # 1.
    registered_names = charm_client.list_registered_names(include_collaborations=True)
    for name in registered_names:
        if name.name == charmhub_charm_name:
            break
    else:
        charm_client.register_name(charmhub_charm_name, entity_type="charm")

    # 2.
    upload_ids = [charm_client.upload_file(filepath=charm) for charm in fake_charms]
    revision_status_urls = [
        charm_client.notify_revision(
            name=charmhub_charm_name,
            revision_request=revisions_model.RevisionsRequestModel(upload_id=upload_id),
        ).status_url
        for upload_id in upload_ids
    ]

    timeout = time.monotonic() + 120
    while True:
        revision_statuses = [
            # Replace this with list_upload_reviews when working on
            # https://github.com/canonical/craft-store/issues/138
            charm_client.request("GET", charm_client._base_url + status_url).json()
            for status_url in revision_status_urls
        ]
        for status in revision_statuses:
            if status["revisions"][0]["status"] not in ("approved", "rejected"):
                time.sleep(2)  # Checking every 2 seconds seems reasonable
                break  # out of the for loop
        else:
            break  # out of the while loop
        if time.monotonic() >= timeout:
            raise TimeoutError(
                "Waited over 120 seconds, charm uploads still neither approved nor rejected",
                revision_statuses,
            )

    revisions_numbers = [
        status["revisions"][0]["revision"] for status in revision_statuses
    ]

    if None in revisions_numbers:
        raise AssertionError(
            "One or more revisions did not get a number", revision_statuses
        )
