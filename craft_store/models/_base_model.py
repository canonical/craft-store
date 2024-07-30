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

"""BaseModel with marshaling capabilities."""

from typing import Any, TypeVar

from pydantic import ConfigDict, BaseModel

Model = TypeVar("Model")


class MarshableModel(BaseModel):
    """A BaseModel that can be marshaled and unmarshaled."""
    # TODO[pydantic]: The following keys were removed: `allow_mutation`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(validate_assignment=True, allow_mutation=False, alias_generator=lambda s: s.replace("_", "-"), populate_by_name=True)

    @classmethod
    def unmarshal(cls: type[Model], data: dict[str, Any]) -> Model:
        """Create and populate a new ``MarshableModel`` from a dict.

        The unmarshal method validates entries in the input dictionary, populating
        the corresponding fields in the data object.

        :param data: The dictionary data to unmarshal.

        :return: The newly created object.

        :raise TypeError: If data is not a dictionary.
        """
        if not isinstance(data, dict):
            raise TypeError("part data is not a dictionary")

        return cls(**data)

    def marshal(self) -> dict[str, Any]:
        """Create a dictionary containing the part specification data.

        :return: The newly created dictionary.

        """
        return self.dict(by_alias=True, exclude_unset=True)
