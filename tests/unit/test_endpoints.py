# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Canonical Ltd.
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


from craft_store import endpoints


def test_charmhub():
    charmhub = endpoints.CHARMHUB

    assert charmhub.tokens == "/v1/tokens"
    assert charmhub.tokens_exchange == "/v1/tokens/exchange"
    assert charmhub.whoami == "/v1/whoami"
    assert charmhub.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
    ) == {
        "permissions": ["permission-foo", "permission-bar"],
        "description": "client description",
        "ttl": 1000,
    }


def test_snap_store():
    snap_store = endpoints.SNAP_STORE

    assert snap_store.tokens == "/api/v2/tokens"
    assert snap_store.tokens_exchange == "/api/v2/tokens/exchange"
    assert snap_store.whoami == "/api/v2/tokens/whoami"
    assert snap_store.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
    ) == {
        "attenuations": ["permission-foo", "permission-bar"],
        "description": "client description",
        "expiry": 1000,
    }
