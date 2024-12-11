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


from typing import cast

import pytest
from craft_store.models import revisions_model

from .conftest import needs_charmhub_credentials

pytestmark = pytest.mark.timeout(10)  # Timeout if any test takes over 10 sec.


@needs_charmhub_credentials()
@pytest.mark.slow
def test_charm_upload(charm_client, fake_charm_file, charmhub_charm_name):
    upload_id = charm_client.upload_file(filepath=fake_charm_file)

    request_model = revisions_model.RevisionsRequestModel(**{"upload-id": upload_id})

    model_response = cast(
        revisions_model.RevisionsResponseModel,
        charm_client.notify_revision(
            name=charmhub_charm_name,
            revision_request=request_model,
        ),
    )

    assert (
        model_response.status_url
        == f"/v1/charm/{charmhub_charm_name}/revisions/review?upload-id={upload_id}"
    )
