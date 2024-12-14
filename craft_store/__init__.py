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

__version__ = "3.0.0"


from . import creds, endpoints, errors, models
from ._httpx_auth import CandidAuth, DeveloperTokenAuth
from .publisher import PublisherGateway
from .auth import Auth
from .base_client import BaseClient
from .http_client import HTTPClient
from .store_client import StoreClient
from .ubuntu_one_store_client import UbuntuOneStoreClient

__all__ = [
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
