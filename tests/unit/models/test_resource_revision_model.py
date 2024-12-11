# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023-2024 Canonical Ltd.
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
"""Tests for resource revision models."""

import pydantic
import pytest
from craft_store.models import CharmResourceRevisionUpdateRequest


@pytest.mark.parametrize(
    ("request_dict", "match"),
    [
        ({"revision": 1}, r"bases[:\s]+Field required"),
        (
            {"revision": 1, "bases": []},
            r"bases[:\s]+List should have at least 1 item",
        ),
        (
            {"revision": 1, "bases": [{"architectures": ["all", "all"]}]},
            r"bases.0.architectures[:\s]+Value error, Duplicate values in list:",
        ),
        (
            {"revision": 1, "bases": [{"architectures": []}]},
            r"bases.0.architectures[:\s]+List should have at least 1 item",
        ),
    ],
)
def test_charmresourcerevisionupdaterequest_invalid_bases(request_dict, match):
    with pytest.raises(pydantic.ValidationError, match=match):
        CharmResourceRevisionUpdateRequest.unmarshal(request_dict)
