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

"""Common Models between namespaces for List Releases responses."""

from ._base_model import MarshableModel


class ProgressiveModel(MarshableModel):
    """Model for the progressive information from the channel-map model.

    :param paused: signals if the progressive release is paused on a channel.
    :param percentage: the progress of a progressive release on a channel.
    """

    paused: bool | None = None
    percentage: float | None = None


class ChannelsModel(MarshableModel):
    """Model for the channels results from the list_releases endpoint.

    :param branch: the channel branch.
    :param fallback: the channel to fallback to if this one is closed.
    :param name: the full name of the channel (<track>/<risk>[/<branch>]).
    :param risk: the channel risk (one of stable, candidate, beta or edge).
    :param track: the channel track.
    """

    branch: str | None = None
    fallback: str | None = None
    name: str
    risk: str
    track: str


class PackageModel(MarshableModel):
    """Model for the package results from the list_releases endpoint.

    :param channels: list of :attr:`ChannelsModel`.
    """

    channels: list[ChannelsModel]
