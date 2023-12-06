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
import datetime
from unittest.mock import Mock

import pydantic
import pytest
import requests
from craft_store import BaseClient, endpoints
from craft_store.models import AccountModel, RegisteredNameModel
from craft_store.models._charm_model import CharmBaseModel
from craft_store.models._snap_models import Confinement, Grade, Type
from craft_store.models.resource_revision_model import (
    CharmResourceBase,
    CharmResourceBaseList,
    CharmResourceRevision,
    CharmResourceType,
)
from craft_store.models.revisions_model import (
    CharmRevisionModel,
    GitRevisionModel,
    SnapRevisionModel,
)

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
    **{"display-name": "Charmhub Publisher"},
)


class ConcreteTestClient(BaseClient):
    def _get_authorization_header(self) -> str:
        return "I am authorised."

    def _get_discharged_macaroon(
        self, root_macaroon: str, **kwargs  # noqa: ARG002
    ) -> str:
        return "The voltmeter reads 0V over this macaroon."


@pytest.fixture()
def charm_client():
    client = ConcreteTestClient(
        base_url="https://staging.example.com",
        storage_base_url="https://storage.staging.example.com",
        endpoints=endpoints.CHARMHUB,
        application_name="testcraft",
        user_agent="craft-store unit tests, should not be hitting a real server",
    )
    client.http_client = Mock(spec=client.http_client)
    return client


@pytest.mark.parametrize(
    ("content", "expected"),
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


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(b'{"revisions":[]}', [], id="empty"),
        pytest.param(
            b"""{"revisions":[{
                "commit-id": "abc",
                "created-at": "2000-01-01T00:00:00",
                "created-by": "lengau",
                "revision": 1,
                "sha3-384": "its_a_fake",
                "status": "statusy"
            }]}""",
            [
                GitRevisionModel(
                    created_at=datetime.datetime(2000, 1, 1, 0, 0, 0),
                    revision=1,
                    sha3_384="its_a_fake",
                    status="statusy",
                    commit_id="abc",
                    created_by="lengau",
                )
            ],
            id="git-revision",
        ),
        pytest.param(
            b"""{"revisions":[{
                "created-at": "2000-01-01T00:00:00",
                "revision": 1,
                "sha3-384": "its_a_fake",
                "status": "statusy",
                "bases": [{"name": "all", "channel": "all", "architecture": "all"}],
                "size": 1234,
                "version": "1.0.0-0-0"
            }]}""",
            [
                CharmRevisionModel(
                    created_at=datetime.datetime(2000, 1, 1, 0, 0, 0),
                    revision=1,
                    sha3_384="its_a_fake",
                    status="statusy",
                    size=1234,
                    version="1.0.0-0-0",
                    bases=[
                        CharmBaseModel(name="all", channel="all", architecture="all")
                    ],
                )
            ],
            id="charm-revision",
        ),
        pytest.param(
            b"""{"revisions":[{
                "created-at": "2000-01-01T00:00:00",
                "revision": 1,
                "sha3-384": "its_a_fake",
                "status": "statusy",
                "apps": ["appy-mc-app-face"],
                "architectures": ["riscv64"],
                "base": "core24",
                "confinement": "strict",
                "created-by": "lengau",
                "grade": "stable",
                "size": 54321,
                "type": "app",
                "version": "1.2.3"
            }]}""",
            [
                SnapRevisionModel(
                    created_at=datetime.datetime(2000, 1, 1, 0, 0, 0),
                    revision=1,
                    sha3_384="its_a_fake",
                    status="statusy",
                    apps=["appy-mc-app-face"],
                    architectures=["riscv64"],
                    base="core24",
                    confinement=Confinement.STRICT,
                    created_by="lengau",
                    grade=Grade.STABLE,
                    size=54321,
                    type=Type.APP,
                    version="1.2.3",
                )
            ],
            id="snap-revision",
        ),
    ],
)
def test_list_revisions(charm_client, content, expected):
    charm_client.http_client.request.return_value = response = requests.Response()
    response._content = content

    actual = charm_client.list_revisions("my_name")

    assert actual == expected


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        pytest.param(b'{"revisions":[]}', [], id="empty"),
        pytest.param(
            b"""{"revisions":[{
                "bases": [{"name": "all", "channel": "all", "architectures": ["all"]}],
                "created-at": "1970-01-01T00:00:00",
                "name": "resource",
                "revision": 1,
                "sha256": "a-sha256",
                "sha3-384": "a 384-bit sha3",
                "sha384": "a sha384",
                "sha512": "a sha512",
                "size": 17,
                "type": "file",
                "updated-at": "2020-03-14T00:00:00",
                "updated-by": "lengau"
            }]}""",
            [
                CharmResourceRevision(
                    bases=CharmResourceBaseList([CharmResourceBase()]),
                    created_at=datetime.datetime(1970, 1, 1),
                    name="resource",
                    revision=1,
                    sha256="a-sha256",
                    sha3_384="a 384-bit sha3",
                    sha384="a sha384",
                    sha512="a sha512",
                    size=pydantic.ByteSize(17),
                    type=CharmResourceType.FILE,
                    updated_at=datetime.datetime(2020, 3, 14),
                    updated_by="lengau",
                )
            ],
        ),
    ],
)
def test_list_resource_revisions_success(charm_client, content, expected):
    charm_client.http_client.request.return_value = response = requests.Response()
    response._content = content

    actual = charm_client.list_resource_revisions("my-charm", "resource")

    assert actual == expected


def test_list_resource_revisions_not_implemented():
    """list_resource_revisions is not implemented for non-charm namespaces."""
    client = ConcreteTestClient(
        base_url="https://staging.example.com",
        storage_base_url="https://storage.staging.example.com",
        endpoints=endpoints.SNAP_STORE,
        application_name="testcraft",
        user_agent="craft-store unit tests, should not be hitting a real server",
    )
    client.http_client = Mock(spec=client.http_client)

    with pytest.raises(NotImplementedError):
        client.list_resource_revisions("my-snap", "my-resource")


@pytest.mark.parametrize(
    ("name", "entity_type", "private", "team", "expected_json"),
    [
        pytest.param(
            "test-charm-abcxyz",
            None,
            False,
            None,
            {"name": "test-charm-abcxyz", "private": False},
            id="basic",
        ),
        pytest.param(
            "test-charm-abc123",
            "charm",
            True,
            "starcraft",
            {
                "name": "test-charm-abc123",
                "private": True,
                "type": "charm",
                "team": "starcraft",
            },
            id="all_filled",
        ),
    ],
)
def test_register_name(charm_client, name, entity_type, private, team, expected_json):
    charm_client.request = Mock()
    charm_client.request.return_value.json.return_value = {"id": "abc"}

    charm_client.register_name(
        name, entity_type=entity_type, private=private, team=team
    )

    charm_client.request.assert_called_once_with(
        "POST", "https://staging.example.com/v1/charm", json=expected_json
    )


def test_unregister_name(charm_client):
    charm_client.request = Mock()
    charm_client.request.return_value.json.return_value = {"package-id": "abc"}

    charm_client.unregister_name("test-charm-abcxyz")

    charm_client.request.assert_called_once_with(
        "DELETE", "https://staging.example.com/v1/charm/test-charm-abcxyz"
    )
