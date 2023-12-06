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
"""Resource revision response models for the Store."""
import datetime
from enum import Enum
from typing import List, Optional, Union

import pydantic

from craft_store.models._base_model import MarshableModel


class CharmResourceType(str, Enum):
    """Resource types for OCI images."""

    OCI_IMAGE = "oci-image"
    FILE = "file"


class CharmResourceBase(MarshableModel):
    """A base for a charm resource."""

    name: str = "all"
    channel: str = "all"
    architectures: List[str] = ["all"]


class CharmResourceRevision(MarshableModel):
    """A basic resource revision."""

    bases: List[CharmResourceBase]
    created_at: datetime.datetime
    name: str
    revision: int
    sha256: str
    sha3_384: str
    sha384: str
    sha512: str
    size: pydantic.ByteSize
    type: Union[CharmResourceType, str]
    updated_at: Optional[datetime.datetime] = None
    updated_by: Optional[str] = None
