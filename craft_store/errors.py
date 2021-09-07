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

import logging

import requests
import urllib3  # type: ignore

logger = logging.getLogger(__name__)


class CraftStoreError(Exception):
    """Base class error for craft-store.

    :param brief: Brief description of error.

    :ivar brief: Brief description of error.
    """

    def __init__(self, brief: str) -> None:
        super().__init__()
        self.brief = brief

    def __str__(self) -> str:
        return self.brief


class NetworkError(CraftStoreError):
    """Error to raise on network or infrastructure issues.

    The original exception is used to potentially craft a user friendly
    error message to be used for :attr:`.brief`.

    :param exception: original exception raised.

    :ivar exception: original exception raised.
    :ivar brief: Brief description of error.
    """

    def __init__(self, exception: Exception) -> None:
        try:
            if isinstance(exception.args[0], urllib3.exceptions.MaxRetryError):
                brief = "Maximum retries exceeded trying to reach the store."
            else:
                brief = str(exception)
        except IndexError:
            brief = str(exception)

        super().__init__(brief=brief)


class StoreServerError(CraftStoreError):
    """Error to raise on infrastructure issues from error codes above ``500``.

    :param response: the response from a :class:`requests.Request`.

    :ivar brief: Brief description of error.
    :ivar response: the response from a :class:`requests.Request`.
    """

    def __init__(self, response: requests.Response) -> None:
        self.response = response

        super().__init__(
            "Issue encountered while processing your request: "
            f"[{response.status_code}] {response.reason}."
        )
