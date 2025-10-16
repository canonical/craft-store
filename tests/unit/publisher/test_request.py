# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
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
"""Unit tests for publisher request models."""

import json

import pydantic
import pytest
from craft_store.publisher import (
    BaseDict,
    PackageLinks,
    ResourceType,
)
from craft_store.publisher._request import PushResourceRequest


class TestPackageLinks:
    """Tests for PackageLinks model with Sequence[Annotated[str, MaxLen(2000)]]."""

    def test_package_links_validates_correctly(self):
        """Test that PackageLinks accepts valid data."""
        links = PackageLinks(
            contact=["https://example.com/contact"],
            docs=["https://docs.example.com", "https://docs2.example.com"],
            website=["https://example.com"],
        )

        assert links.contact == ["https://example.com/contact"]
        assert links.docs == ["https://docs.example.com", "https://docs2.example.com"]
        assert links.website == ["https://example.com"]

    def test_package_links_serializes_correctly(self):
        """Test that PackageLinks serializes to correct JSON structure."""
        links = PackageLinks(
            contact=["https://example.com/contact"],
            docs=["https://docs.example.com"],
        )

        # Test model_dump
        dumped = links.model_dump(exclude_none=True)
        assert dumped == {
            "contact": ["https://example.com/contact"],
            "docs": ["https://docs.example.com"],
        }

        # Test JSON serialization via model_dump_json
        json_str = links.model_dump_json(exclude_none=True)
        parsed = json.loads(json_str)
        assert parsed == {
            "contact": ["https://example.com/contact"],
            "docs": ["https://docs.example.com"],
        }

    def test_package_links_accepts_tuple(self):
        """Test that PackageLinks accepts tuple (Sequence subtype)."""
        links = PackageLinks(
            contact=("https://example.com/contact",),
            docs=("https://docs.example.com", "https://docs2.example.com"),
        )

        # Pydantic preserves the Sequence type (tuple)
        dumped = links.model_dump(exclude_none=True)
        assert dumped["contact"] == ("https://example.com/contact",)
        assert dumped["docs"] == (
            "https://docs.example.com",
            "https://docs2.example.com",
        )

    def test_package_links_rejects_url_too_long(self):
        """Test that URLs exceeding 2000 characters are rejected."""
        long_url = "https://example.com/" + "a" * 2000  # Over 2000 chars

        with pytest.raises(pydantic.ValidationError) as exc_info:
            PackageLinks(contact=[long_url])

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "contact" in str(errors[0]["loc"])
        assert "String should have at most 2000 characters" in errors[0]["msg"]

    def test_package_links_accepts_max_length_url(self):
        """Test that URLs at exactly 2000 characters are accepted."""
        # Create a URL that's exactly 2000 characters
        base = "https://example.com/"
        padding = "a" * (2000 - len(base))
        max_url = base + padding

        assert len(max_url) == 2000

        links = PackageLinks(contact=[max_url])
        assert links.contact == [max_url]

    def test_package_links_all_fields_none(self):
        """Test that all fields can be None."""
        links = PackageLinks()

        assert links.contact is None
        assert links.docs is None
        assert links.donations is None
        assert links.issues is None
        assert links.source is None
        assert links.website is None

        dumped = links.model_dump(exclude_none=True)
        assert dumped == {}

    def test_package_links_multiple_fields(self):
        """Test that multiple fields can be set simultaneously."""
        links = PackageLinks(
            contact=["mailto:contact@example.com"],
            docs=["https://docs.example.com"],
            donations=["https://donate.example.com"],
            issues=["https://github.com/example/repo/issues"],
            source=["https://github.com/example/repo"],
            website=["https://example.com", "https://www.example.com"],
        )

        dumped = links.model_dump(exclude_none=True)
        assert len(dumped) == 6
        assert dumped["contact"] == ["mailto:contact@example.com"]
        assert dumped["website"] == ["https://example.com", "https://www.example.com"]


class TestBaseDict:
    """Tests for BaseDict TypedDict structure."""

    def test_base_dict_structure(self):
        """Test that BaseDict has the correct structure."""
        base: BaseDict = {
            "name": "ubuntu",
            "channel": "20.04",
            "architectures": ["amd64"],
        }

        assert base["name"] == "ubuntu"
        assert base["channel"] == "20.04"
        assert base["architectures"] == ["amd64"]

    def test_base_dict_multiple_architectures(self):
        """Test that BaseDict accepts multiple architectures."""
        base: BaseDict = {
            "name": "ubuntu",
            "channel": "22.04",
            "architectures": ["amd64", "arm64", "s390x"],
        }

        assert len(base["architectures"]) == 3
        assert "amd64" in base["architectures"]
        assert "arm64" in base["architectures"]
        assert "s390x" in base["architectures"]


class TestResourceType:
    """Tests for ResourceType enum."""

    def test_resource_type_enum_values(self):
        """Test that ResourceType enum has correct values."""
        assert ResourceType.FILE.value == "file"
        assert ResourceType.OCI_IMAGE.value == "oci-image"
        assert ResourceType.COMPONENT_TEST.value == "component/test"
        assert ResourceType.COMPONENT_KERNEL_MODULES.value == "component/kernel-modules"
        assert ResourceType.COMPONENT_STANDARD.value == "component/standard"

    def test_resource_type_enum_membership(self):
        """Test that we can check ResourceType membership."""
        assert "file" in [rt.value for rt in ResourceType]
        assert "oci-image" in [rt.value for rt in ResourceType]
        assert "invalid-type" not in [rt.value for rt in ResourceType]

    def test_resource_type_string_comparison(self):
        """Test that ResourceType can be compared with strings."""
        assert ResourceType.FILE.value == "file"
        assert ResourceType.OCI_IMAGE.value == "oci-image"

    def test_resource_type_serialization(self):
        """Test that ResourceType can be serialized."""
        request = PushResourceRequest(
            upload_id="test-123", type=ResourceType.FILE, bases=None
        )

        dumped = request.model_dump(exclude_none=True)
        assert dumped["type"] == "file"

    def test_resource_type_deserialization(self):
        """Test that ResourceType can be deserialized from string."""
        request = PushResourceRequest.model_validate(
            {"upload_id": "test-123", "type": "oci-image"}
        )

        assert request.type == ResourceType.OCI_IMAGE
