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

"""Revisions response models for the Store."""

from ._base_model import MarshableModel


class RevisionsRequestModel(MarshableModel):
    """Resource model for a ReleaseRequestModel.

    :param upload_id: the upload-id returned from the storage endpoint.
    """

    upload_id: str


class RevisionsResponseModel(MarshableModel):
    """Model for a revisions response.

    :param status-url: a URL to monitor the state of the posted revision.
    """

    status_url: str
