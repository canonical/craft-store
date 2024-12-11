# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021,2024 Canonical Ltd.
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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""Interact with Canonical services such as Charmhub and the Snap Store."""

from . import creds, endpoints, errors, models
from ._httpx_auth import CandidAuth, DeveloperTokenAuth
from .publisher import PublisherGateway
from .auth import Auth
from .base_client import BaseClient
from .http_client import HTTPClient
from .store_client import StoreClient
from .ubuntu_one_store_client import UbuntuOneStoreClient


try:
    from ._version import __version__
except ImportError:  # pragma: no cover
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("craft-store")
    except PackageNotFoundError:
        __version__ = "dev"


__all__ = [
    "__version__",
    "creds",
    "endpoints",
    "errors",
    "models",
    "PublisherGateway",
    "Auth",
    "BaseClient",
    "CandidAuth",
    "HTTPClient",
    "StoreClient",
    "UbuntuOneStoreClient",
    "DeveloperTokenAuth",
]
