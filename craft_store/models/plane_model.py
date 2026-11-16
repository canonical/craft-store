# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2025 Canonical Ltd.
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

"""Models for Source Store plane."""

from typing_extensions import Self

from craft_store.errors import IncorrectPlaneError
from craft_store.models._base_model import MarshableModel


class Plane(MarshableModel):
    """Class representing specific plane."""

    domain_name: str
    plane_name: str

    @property
    def name(self) -> str:
        """Return the plane name in domain/plane format."""
        return f"{self.domain_name}/{self.plane_name}"

    @classmethod
    def from_str(cls, val: str) -> Self:
        """Create a Plane from a string in domain/plane format."""
        try:
            domain_name, plane_name = val.split("/")
        except ValueError:
            raise IncorrectPlaneError(f"Cannot create Plane object from: {val!r}")
        else:
            return cls(domain_name=domain_name, plane_name=plane_name)
