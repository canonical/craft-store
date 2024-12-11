#  -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*
#
#  Copyright 2023 Canonical Ltd.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License version 3 as published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""Basic snap-related models."""

from enum import Enum


class Confinement(str, Enum):
    """Snap confinement."""

    CLASSIC = "classic"
    STRICT = "strict"
    DEVMODE = "devmode"


class Grade(str, Enum):
    """Snap grade."""

    DEVEL = "devel"
    STABLE = "stable"


class Type(str, Enum):
    """Type of snap."""

    APP = "app"
    GADGET = "gadget"
    KERNEL = "kernel"
    BASE = "base"
    SNAPD = "snapd"
