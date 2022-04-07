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

import shutil
from pathlib import Path

import pytest
import yaml

from craft_store import StoreClient, endpoints


@pytest.fixture
def charm_client():
    """A common StoreClient for charms"""
    return StoreClient(
        application_name="integration-test",
        base_url="https://api.staging.charmhub.io",
        storage_base_url="https://storage.staging.snapcraftcontent.com",
        endpoints=endpoints.CHARMHUB,
        user_agent="integration-tests",
        environment_auth="CRAFT_STORE_CHARMCRAFT_CREDENTIALS",
    )


@pytest.fixture
def fake_charm_file(tmpdir):
    """Provide a fake charm to upload to charmhub."""
    # Make tmpdir Path instead of Path-like.
    prime_dir = Path(tmpdir) / "prime"
    prime_dir.mkdir()

    medadata_path = prime_dir / "metadata.yaml"
    with medadata_path.open("w") as metadata_file:
        yaml.safe_dump(
            data={
                "name": "craft-store-test-charm",
                "display-name": "display",
                "description": "description",
                "summary": "summary",
            },
            stream=metadata_file,
        )

    manifest_path = prime_dir / "manifest.yaml"
    with manifest_path.open("w") as manifest_file:
        yaml.safe_dump(
            data={
                "analysis": {
                    "attributes": [
                        {
                            "name": "language",
                            "result": "python",
                        },
                        {
                            "name": "framework",
                            "result": "operator",
                        },
                    ]
                },
                "bases": [
                    {
                        "architectures": ["amd64"],
                        "channel": "22.04",
                        "name": "ubuntu",
                    }
                ],
                "charmcraft-started-at": "2022-04-03T22:27:43.044456Z",
                "charmcraft-version": "1.5.0+12.g04477df.dirty",
            },
            stream=manifest_file,
        )

        charm_file = Path(tmpdir) / "test.charm"
        Path(shutil.make_archive(str(charm_file), "zip", str(prime_dir))).rename(
            charm_file
        )

        return charm_file
