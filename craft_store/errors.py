# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Canonical Ltd.
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

"""Craft Store errors."""

import dataclasses
import logging

import requests
import urllib3  # type: ignore

logger = logging.getLogger(__name__)


class CraftStoreError(Exception):
    """Base class error for craft-store."""


@dataclasses.dataclass(repr=True)
class NetworkError(CraftStoreError):
    """Error to raise on network or infrastructure issues.

    The original exception is used to potentially craft a user friendly
    error message to be used for :attr:`.brief`.

    :param exception: original exception raised.

    :ivar brief: Brief description of error.
    """

    brief: str = dataclasses.field(init=False)
    exception: Exception

    def __post_init__(self) -> None:
        try:
            if isinstance(self.exception.args[0], urllib3.exceptions.MaxRetryError):
                brief = "Maximum retries exceeded trying to reach the store."
            else:
                brief = str(self.exception)
        except IndexError:
            brief = str(self.exception)

        self.brief = brief

    def __str__(self) -> str:
        return self.brief


@dataclasses.dataclass(repr=True)
class StoreServerError(CraftStoreError):
    """Error to raise on infrastructure issues from error codes above ``500``.

    :param response: the response from a :class:`requests.Request`.

    :ivar brief: Brief description of error.
    :ivar response: the response from a :class:`requests.Request`.
    """

    brief: str = dataclasses.field(init=False)
    response: requests.Response

    def __post_init__(self) -> None:
        self.brief = (
            "Issue encountered while processing your request: "
            f"[{self.response.status_code}] {self.response.reason}."
        )

    def __str__(self) -> str:
        return self.brief
