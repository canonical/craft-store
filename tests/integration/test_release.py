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

import pytest

from craft_store import StoreClient, endpoints
from craft_store.models import release_request_model


@pytest.mark.skipif(
    os.getenv("CRAFT_STORE_CHARMCRAFT_CREDENTIALS") is None,
    reason="CRAFT_STORE_CHARMCRAFT_CREDENTIALS are not set",
)
def test_charm_release():
    client = StoreClient(
        application_name="integration-test",
        base_url="https://api.charmhub.io",
        storage_base_url="https://storage.charmhub.io",
        endpoints=endpoints.CHARMHUB,
        user_agent="integration-tests",
        environment_auth="CRAFT_STORE_CHARMCRAFT_CREDENTIALS",
    )

    model = release_request_model.ReleaseRequestModel(
        channel="edge", revision=1, resources=[]
    )

    client.release(
        name="craft-store-test-charm",
        release_request=[model],
    )
