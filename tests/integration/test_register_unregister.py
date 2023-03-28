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


import datetime
import os

import pytest


@pytest.mark.skipif(
    not os.getenv("CRAFT_STORE_CHARMCRAFT_CREDENTIALS"),
    reason="CRAFT_STORE_CHARMCRAFT_CREDENTIALS are not set",
)
def test_register_unregister_cycle(charm_client):
    whoami = charm_client.whoami()
    account_id = whoami.get("account", {}).get("id").lower()
    timestamp_us = int(datetime.datetime.utcnow().timestamp() * 1_000_000)
    charm_name = f"test-charm-{account_id}-{timestamp_us}"

    names = [result.name for result in charm_client.list_registered_names()]
    assert charm_name not in names, "Charm name already registered, test setup failed."

    charm_client.register_name(charm_name, entity_type="charm")

    names = [result.name for result in charm_client.list_registered_names()]
    assert charm_name in names, "Charm was not successfully registered."

    charm_client.unregister_name(charm_name)

    names = [result.name for result in charm_client.list_registered_names()]
    assert charm_name not in names, "Charm was not successfully unregistered."
