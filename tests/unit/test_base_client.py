#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*
#
#  Copyright 2023 Canonical Ltd.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License version 3 as published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""Tests for methods in the BaseClient class."""
from unittest.mock import Mock

import pytest
import requests

from craft_store import BaseClient, endpoints
from craft_store.models import RegisteredNameModel, AccountModel

SAMPLE_REAL_REGISTERED_NAMES = b"""{
  "results": [
    {
      "authority": null,
      "contact": null,
      "default-track": null,
      "description": null,
      "id": "test1id",
      "links": {},
      "media": [],
      "name": "test-charm",
      "private": false,
      "publisher": {
        "display-name": "Charmhub Publisher",
        "id": "pubid",
        "username": "usso-someone",
        "validation": "unproven"
      },
      "status": "registered",
      "store": "ubuntu",
      "summary": null,
      "title": null,
      "track-guardrails": [],
      "tracks": [],
      "type": "charm",
      "website": null
    }
  ]
}
"""
DEMO_ACCOUNT = AccountModel(
    id="pubid",
    username="usso-someone",
    validation="unproven",
    **{"display-name": "Charmhub Publisher"}
)


class ConcreteTestClient(BaseClient):
    def _get_authorization_header(self) -> str:
        return "I am authorised."

    def _get_discharged_macaroon(self, root_macaroon: str, **kwargs) -> str:
        return "The voltmeter reads 0V over this macaroon."


@pytest.fixture
def charm_client():
    client = ConcreteTestClient(
        base_url="https://staging.example.com",
        storage_base_url="https://storage.staging.example.com",
        endpoints=endpoints.CHARMHUB,
        application_name="testcraft",
        user_agent="craft-store unit tests, should not be hitting a real server",
    )
    client.http_client = Mock(spec=client.http_client)
    yield client


@pytest.mark.parametrize(
    "content,expected",
    [
        (b'{"results":[]}', []),
        (
            SAMPLE_REAL_REGISTERED_NAMES,
            [
                RegisteredNameModel(
                    id="test1id",
                    name="test-charm",
                    private=False,
                    publisher=DEMO_ACCOUNT,
                    status="registered",
                    store="ubuntu",
                    type="charm",
                ),
            ],
        ),
    ],
)
def test_list_registered_names(charm_client, content, expected):
    charm_client.http_client.request.return_value = response = requests.Response()
    response._content = content
    actual = charm_client.list_registered_names()

    assert actual == expected
