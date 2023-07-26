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

import pytest
from craft_store import endpoints


def test_charmhub():
    charmhub = endpoints.CHARMHUB

    assert charmhub.tokens == "/v1/tokens"
    assert charmhub.tokens_exchange == "/v1/tokens/exchange"
    assert charmhub.whoami == "/v1/tokens/whoami"
    assert charmhub.upload == "/unscanned-upload/"
    assert charmhub.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
    ) == {
        "permissions": ["permission-foo", "permission-bar"],
        "description": "client description",
        "ttl": 1000,
    }


def test_charmhub_channels():
    charmhub = endpoints.CHARMHUB

    assert charmhub.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
        channels=["stable", "track/edge"],
    ) == {
        "permissions": ["permission-foo", "permission-bar"],
        "description": "client description",
        "ttl": 1000,
        "channels": ["stable", "track/edge"],
    }


def test_charmhub_packages():
    charmhub = endpoints.CHARMHUB

    assert charmhub.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
        packages=[
            endpoints.Package("charm1", "charm"),
            endpoints.Package("bundle1", "bundle"),
        ],
    ) == {
        "permissions": ["permission-foo", "permission-bar"],
        "description": "client description",
        "ttl": 1000,
        "packages": [
            {"type": "charm", "name": "charm1"},
            {"type": "bundle", "name": "bundle1"},
        ],
    }


def test_charmhub_invalid_packages():
    charmhub = endpoints.CHARMHUB

    with pytest.raises(ValueError) as raised:  # noqa: PT011
        charmhub.get_token_request(
            permissions=["permission-foo", "permission-bar"],
            description="client description",
            ttl=1000,
            packages=[
                endpoints.Package("charm1", "snap"),
                endpoints.Package("bundle1", "rock"),
            ],
        )
    assert (
        str(raised.value) == "Package types ['snap', 'rock'] not in ['charm', 'bundle']"
    )


def test_charmhub_releases():
    charmhub = endpoints.CHARMHUB

    assert (
        charmhub.get_releases_endpoint("test-charm") == "/v1/charm/test-charm/releases"
    )


def test_charmhub_revisions():
    charmhub = endpoints.CHARMHUB

    assert (
        charmhub.get_revisions_endpoint("test-charm")
        == "/v1/charm/test-charm/revisions"
    )


def test_snap_store(expires):
    snap_store = endpoints.SNAP_STORE

    assert snap_store.tokens == "/api/v2/tokens"
    assert snap_store.tokens_exchange == "/api/v2/tokens/exchange"
    assert snap_store.whoami == "/api/v2/tokens/whoami"
    assert snap_store.upload == "/unscanned-upload/"
    assert snap_store.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
    ) == {
        "permissions": ["permission-foo", "permission-bar"],
        "description": "client description",
        "expires": expires(1000),
    }


def test_snap_store_channels(expires):
    snap_store = endpoints.SNAP_STORE

    assert snap_store.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
        channels=["stable", "track/edge"],
    ) == {
        "permissions": ["permission-foo", "permission-bar"],
        "description": "client description",
        "expires": expires(1000),
        "channels": ["stable", "track/edge"],
    }


def test_snap_store_packages(expires):
    snap_store = endpoints.SNAP_STORE

    assert snap_store.get_token_request(
        permissions=["permission-foo", "permission-bar"],
        description="client description",
        ttl=1000,
        packages=[
            endpoints.Package("snap1", "snap"),
            endpoints.Package("snap2", "snap"),
        ],
    ) == {
        "permissions": ["permission-foo", "permission-bar"],
        "description": "client description",
        "expires": expires(1000),
        "packages": [
            {"series": "16", "name": "snap1"},
            {"series": "16", "name": "snap2"},
        ],
    }


def test_snap_store_invalid_packages():
    snap_store = endpoints.SNAP_STORE

    with pytest.raises(ValueError) as raised:  # noqa: PT011
        snap_store.get_token_request(
            permissions=["permission-foo", "permission-bar"],
            description="client description",
            ttl=1000,
            packages=[
                endpoints.Package("snap1", "charm"),
                endpoints.Package("snap2", "rock"),
            ],
        )
    assert str(raised.value) == "Package types ['charm', 'rock'] not in ['snap']"


def test_snap_store_releases():
    snap_store = endpoints.SNAP_STORE

    with pytest.raises(NotImplementedError):
        snap_store.get_releases_endpoint("test-snap")


def test_snap_store_revisions():
    snap_store = endpoints.SNAP_STORE

    with pytest.raises(NotImplementedError):
        snap_store.get_revisions_endpoint("test-snap")
