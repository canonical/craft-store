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
"""Full workflow tests for charms."""

import datetime
import hashlib
import time

import pytest
from craft_store.models import revisions_model
from craft_store.models.resource_revision_model import (
    CharmResourceRevisionUpdateRequest,
    CharmResourceType,
    RequestCharmResourceBase,
    ResponseCharmResourceBase,
)

from tests.integration.conftest import needs_charmhub_credentials


@needs_charmhub_credentials()
@pytest.mark.slow
# This is intentionally long since it goes through a full workflow
def test_full_charm_workflow(  # noqa: PLR0912, PLR0915
    tmp_path, charm_client, charmhub_charm_name, fake_charms
):
    """A full workflow test for uploading a charm.

    Steps include:
    1. Check if charm name is registered.
       1.1. Register if necessary.
    2. Upload one or more charm revisions
    3. Upload one or more OCI images (must already exist on disk) - TODO
    4. Upload a fresh file
    5. Upload an empty file
    6. Modify the bases for a resource.
    """
    # 1.
    charmhub_charm_name += "-workflow"
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

    # 3. Rocks!
    # TODO: This requires the docker registry and stuff

    # Prep for file upload stuff
    arch_dependent_base = RequestCharmResourceBase(architectures=["amd64"])
    neutral_base = RequestCharmResourceBase(architectures=["all"])

    # 4. Upload a fresh file.
    fresh_file = tmp_path / "fresh_file"
    file_contents = datetime.datetime.now(tz=datetime.timezone.utc).isoformat().encode()
    fresh_file.write_bytes(file_contents)
    file_upload_id = charm_client.upload_file(filepath=fresh_file)
    file_status_url = charm_client.push_resource(
        charmhub_charm_name,
        "my-file",
        upload_id=file_upload_id,
        resource_type=CharmResourceType.FILE,
        bases=[arch_dependent_base],
    )  # Response is a list_upload_reviews path + query parameter.
    timeout = time.monotonic() + 120
    while True:
        file_status = charm_client.request(
            "GET", charm_client._base_url + file_status_url
        ).json()["revisions"][0]
        if file_status["status"] in ("approved", "rejected"):
            break
        if time.monotonic() > timeout:
            raise TimeoutError(
                "File upload was not approved or rejected after 120s", file_status
            )
        time.sleep(2)
    assert file_status["revision"] is not None
    file_revisions = charm_client.list_resource_revisions(
        name=charmhub_charm_name, resource_name="my-file"
    )
    for file_revision in file_revisions:
        if file_revision.revision == file_status["revision"]:
            break
    else:
        raise ValueError("File revision from status URL does not appear in revisions.")

    file_sha256 = hashlib.sha256(file_contents).hexdigest()
    assert file_revision.size == len(file_contents), (
        "Uploaded file size does not match file."
    )
    assert file_revision.sha256 == file_sha256, (
        "Uploaded file hash does not match file."
    )
    assert file_revision.bases == [arch_dependent_base]

    # 5. Upload a zero-byte file (probably a repeat)
    zero_byte_file = tmp_path / "zero_bytes"
    zero_byte_file.touch()
    file_upload_id = charm_client.upload_file(filepath=zero_byte_file)
    file_status_url = charm_client.push_resource(
        charmhub_charm_name,
        "my-file",
        upload_id=file_upload_id,
        resource_type=CharmResourceType.FILE,
        bases=[arch_dependent_base],
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
        name=charmhub_charm_name, resource_name="my-file"
    )
    for zb_file_revision in file_revisions:
        if zb_file_revision.revision == file_status["revision"]:
            break
    else:
        raise ValueError(
            "Zero-byte file revision from status URL does not appear in revisions."
        )
    assert zb_file_revision.size == 0
    assert zb_file_revision.sha3_384 == hashlib.sha3_384(b"").hexdigest()
    assert "amd64" in zb_file_revision.bases[0].architectures

    # 6. Modify bases for the files.
    assert (
        charm_client.update_resource_revisions(
            CharmResourceRevisionUpdateRequest(
                revision=file_revision.revision,
                bases=[arch_dependent_base, neutral_base],
            ),
            CharmResourceRevisionUpdateRequest(
                revision=zb_file_revision.revision,
                bases=[arch_dependent_base, neutral_base],
            ),
            name=charmhub_charm_name,
            resource_name="my-file",
        )
        == 2
    )
    file_revisions = charm_client.list_resource_revisions(
        name=charmhub_charm_name, resource_name="my-file"
    )
    new_zb_revision = None
    new_revision = None
    for rev in file_revisions:
        if rev.revision == zb_file_revision.revision:
            new_zb_revision = rev
        if rev.revision == file_revision.revision:
            new_revision = rev
        if new_revision and new_zb_revision:
            break
    assert new_revision is not None, "File revision not found in resource revisions"
    assert new_zb_revision is not None, (
        "Zero-byte file revision not found in resource revisions"
    )
    combined_base = ResponseCharmResourceBase(
        name="all", channel="all", architectures=["amd64", "all"]
    )
    assert new_revision.bases == [combined_base]
    assert new_zb_revision.bases == [combined_base]

    charm_client.update_resource_revision(
        charmhub_charm_name,
        "my-file",
        revision=zb_file_revision.revision,
        bases=[neutral_base],
    )
    file_revisions = charm_client.list_resource_revisions(
        name=charmhub_charm_name, resource_name="my-file"
    )
    for rev in file_revisions:
        if rev.revision == zb_file_revision.revision:
            break
    else:
        raise ValueError("No file with the appropriate revision found")
    assert rev.bases == [neutral_base]
