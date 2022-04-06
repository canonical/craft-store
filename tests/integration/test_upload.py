# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
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


import os
from typing import cast

import pytest

from craft_store.models import revisions_model


@pytest.mark.skipif(
    os.getenv("CRAFT_STORE_CHARMCRAFT_CREDENTIALS") is None,
    reason="CRAFT_STORE_CHARMCRAFT_CREDENTIALS are not set",
)
def test_charm_upload(charm_client, fake_charm_file):
    upload_id = charm_client.upload_file(filepath=fake_charm_file)

    request_model = revisions_model.RevisionsRequestModel(**{"upload-id": upload_id})

    model_response = cast(
        revisions_model.RevisionsResponseModel,
        charm_client.notify_revision(
            name="craft-store-test-charm",
            revision_request=request_model,
        ),
    )

    assert (
        model_response.status_url
        == f"/v1/charm/craft-store-test-charm/revisions/review?upload-id={upload_id}"
    )
