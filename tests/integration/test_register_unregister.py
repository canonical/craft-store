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

import pytest
from craft_store.errors import StoreServerError

from .conftest import needs_charmhub_credentials

pytestmark = pytest.mark.timeout(10)  # Timeout if any test takes over 10 sec.


@needs_charmhub_credentials()
@pytest.mark.slow
@pytest.mark.parametrize("entity_type", ["charm", "bundle"])
def test_register_unregister_cycle(charm_client, unregistered_charm_name, entity_type):
    try:
        charm_client.register_name(unregistered_charm_name, entity_type=entity_type)

        names = {result.name for result in charm_client.list_registered_names()}
        assert unregistered_charm_name in names, (
            f"{entity_type} was not successfully registered."
        )
    finally:
        charm_client.unregister_name(unregistered_charm_name)

    names = {result.name for result in charm_client.list_registered_names()}
    assert unregistered_charm_name not in names, (
        f"{entity_type} was not successfully unregistered."
    )


@needs_charmhub_credentials()
@pytest.mark.slow
def test_unregister_nonexistent(charm_client, unregistered_charm_name):
    with pytest.raises(StoreServerError) as exc_info:
        charm_client.unregister_name(unregistered_charm_name)

    assert "resource-not-found" in exc_info.value.error_list
