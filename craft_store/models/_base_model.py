# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022,2024 Canonical Ltd.
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

"""BaseModel with marshaling capabilities."""

from typing import Any

from pydantic import BaseModel, ConfigDict
from typing_extensions import Self


class MarshableModel(BaseModel):
    """A BaseModel that can be marshaled and unmarshaled."""

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=True,
        alias_generator=lambda s: s.replace("_", "-"),
        populate_by_name=True,
    )

    @classmethod
    def unmarshal(cls, data: dict[str, Any]) -> Self:
        """Create and populate a new ``MarshableModel`` from a dict.

        The unmarshal method validates entries in the input dictionary, populating
        the corresponding fields in the data object.

        :param data: The dictionary data to unmarshal.

        :return: The newly created object.

        :raise TypeError: If data is not a dictionary.
        """
        if not isinstance(data, dict):
            raise TypeError("part data is not a dictionary")

        return cls.model_validate(data)

    def marshal(self) -> dict[str, Any]:
        """Create a dictionary containing the part specification data.

        :return: The newly created dictionary.

        """
        return self.model_dump(mode="json", by_alias=True, exclude_unset=True)
