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

"""Attenuations for Snap Store and Charmhub discharged Macaroons."""

# read/write access.
ACCOUNT_REGISTER_PACKAGE = "account-register-package"
"""Register or request a new package name under a given account."""

PACKAGE_MANAGE = "package-manage"
"""
Meta permission for easing creation of a complete RW token,
it grants all the package-manage-* permissions.
"""

PACKAGE_MANAGE_ACL = "package-manage-acl"
"""Add, invite or remove collaborators."""

PACKAGE_MANAGE_LIBRARY = "package-manage-library"
"""Register or request a new library name under a given package."""

PACKAGE_MANAGE_METADATA = "package-manage-metadata"
"""Edit metadata, add or remove media, etc."""

PACKAGE_MANAGE_RELEASES = "package-manage-releases"
"""
Release revisions, close channels and update version pattern for a track.
"""

PACKAGE_MANAGE_REVISIONS = "package-manage-revisions"
"""
Upload new blobs, check for upload status, reject a revision blocked on
manual review or request manual review.
"""

# read only access.
ACCOUNT_VIEW_PACKAGES = "account-view-packages"
"""
List packages owned by the account and packages for which this account
has collaborator rights.
"""

PACKAGE_VIEW = "package-view"
"""
Meta permission for easing creation of a complete RO token grants all the
package-view-* permissions.
"""

PACKAGE_VIEW_ACL = "package-view-acl"
"""List the collaborators for a package and privacy settings."""

PACKAGE_VIEW_METADATA = "package-view-metadata"
"""View the metadata for a package, including media."""

PACKAGE_VIEW_METRICS = "package-view-metrics"
"""View the metrics of a package."""

PACKAGE_VIEW_RELEASES = "package-view-releases"
"""
List the current releases (channel map) for a package and the release
history of a package.
"""

PACKAGE_VIEW_REVISIONS = "package-view-revisions"
"""List the existing revisions for a package, along with status information."""
