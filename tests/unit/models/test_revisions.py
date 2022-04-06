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

from typing import cast

from craft_store.models import revisions_model


def test_request_unmarshal_and_marshal():
    payload = {
        "upload-id": "fake-id",
    }

    model = cast(
        revisions_model.RevisionsRequestModel,
        revisions_model.RevisionsRequestModel.unmarshal(payload),
    )

    assert model.upload_id == "fake-id"

    assert model.marshal() == payload


def test_response_unmarshal_and_marshal():
    payload = {
        "status-url": "/foo.bar",
    }

    model = cast(
        revisions_model.RevisionsResponseModel,
        revisions_model.RevisionsResponseModel.unmarshal(payload),
    )

    assert model.status_url == "/foo.bar"

    assert model.marshal() == payload
