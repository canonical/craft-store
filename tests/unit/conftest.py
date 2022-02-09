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

import datetime
from unittest.mock import patch

import pytest


@pytest.fixture
def expires():
    """Mocks/freezes utcnow() in craft_store.endpoints module.

    Provides a function for creating expected iso formatted expires datetime
    values.
    """
    now = datetime.datetime.utcnow()

    def offset_iso_dt(seconds=0):
        return (now + datetime.timedelta(seconds=seconds)).replace(
            microsecond=0
        ).isoformat() + "+00:00"

    with patch("craft_store.endpoints.datetime", wraps=datetime.datetime) as dt_mock:
        dt_mock.utcnow.return_value = now
        yield offset_iso_dt
