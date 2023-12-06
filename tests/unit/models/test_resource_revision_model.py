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
"""Tests for resource revision models."""
import pydantic
import pytest
from craft_store.models import CharmResourceRevisionUpdateRequest


@pytest.mark.parametrize(
    "request_dict",
    [
        {"revision": 1},
        {"revision": 1, "bases": []},
        {"revision": 1, "bases": [{"architectures": ["all", "all"]}]},
        {"revision": 1, "bases": [{"architectures": []}]},
    ],
)
def test_charmresourcerevisionupdaterequest_invalid_bases(request_dict):
    with pytest.raises(pydantic.ValidationError):
        CharmResourceRevisionUpdateRequest.unmarshal(request_dict)
