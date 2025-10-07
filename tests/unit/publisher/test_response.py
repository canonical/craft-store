# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
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
"""Unit tests for publisher response models."""

import datetime

import pydantic
import pytest
from craft_store.publisher._response import ExistingMacaroon, GetMacaroonResponse


class TestExistingMacaroon:
    """Tests for ExistingMacaroon model with datetime parsing."""

    def test_revoked_at_parses_datetime_string(self):
        """Test that revoked_at parses valid datetime strings."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_at="2024-06-01T10:00:00Z",
        )

        assert isinstance(macaroon.revoked_at, datetime.datetime)
        assert macaroon.revoked_at.year == 2024
        assert macaroon.revoked_at.month == 6
        assert macaroon.revoked_at.day == 1
        assert macaroon.revoked_at.hour == 10

    def test_revoked_at_parses_datetime_with_microseconds(self):
        """Test that revoked_at parses datetime strings with microseconds."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_at="2024-06-01T10:00:00.123456Z",
        )

        assert isinstance(macaroon.revoked_at, datetime.datetime)
        assert macaroon.revoked_at.microsecond == 123456

    def test_revoked_at_accepts_datetime_object(self):
        """Test that revoked_at accepts datetime objects directly."""
        revoked_time = datetime.datetime(2024, 6, 1, 10, 0, 0)
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_at=revoked_time,
        )

        assert macaroon.revoked_at == revoked_time
        assert isinstance(macaroon.revoked_at, datetime.datetime)

    def test_revoked_at_accepts_none(self):
        """Test that revoked_at can be None."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_at=None,
        )

        assert macaroon.revoked_at is None

    def test_revoked_at_defaults_to_none(self):
        """Test that revoked_at defaults to None when not provided."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
        )

        assert macaroon.revoked_at is None

    def test_revoked_at_fallback_to_string_on_invalid_datetime(self):
        """Test that revoked_at falls back to string if datetime parsing fails."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_at="invalid-datetime-string",
        )

        assert isinstance(macaroon.revoked_at, str)
        assert macaroon.revoked_at == "invalid-datetime-string"

    def test_revoked_at_serialization_with_datetime(self):
        """Test that revoked_at with datetime serializes correctly."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_at="2024-06-01T10:00:00Z",
        )

        dumped = macaroon.model_dump()
        assert "revoked_at" in dumped
        assert isinstance(dumped["revoked_at"], datetime.datetime)

    def test_revoked_at_serialization_with_string(self):
        """Test that revoked_at with string fallback serializes correctly."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_at="invalid-datetime",
        )

        dumped = macaroon.model_dump()
        assert dumped["revoked_at"] == "invalid-datetime"

    def test_existing_macaroon_with_description(self):
        """Test ExistingMacaroon with description field."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            description="Test macaroon for CI/CD",
        )

        assert macaroon.description == "Test macaroon for CI/CD"

    def test_existing_macaroon_with_revoked_by(self):
        """Test ExistingMacaroon with revoked_by field."""
        macaroon = ExistingMacaroon(
            session_id="session-123",
            valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
            valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            revoked_by="admin@example.com",
            revoked_at="2024-06-01T10:00:00Z",
        )

        assert macaroon.revoked_by == "admin@example.com"


class TestGetMacaroonResponse:
    """Tests for GetMacaroonResponse oneOf validation."""

    def test_get_macaroon_with_macaroon_field(self):
        """Test GetMacaroonResponse with only macaroon field."""
        response = GetMacaroonResponse(macaroon="bakery-v2-macaroon-string")

        assert response.macaroon == "bakery-v2-macaroon-string"
        assert response.macaroons is None

    def test_get_macaroon_with_macaroons_field(self):
        """Test GetMacaroonResponse with only macaroons field."""
        macaroons = [
            ExistingMacaroon(
                session_id="session-1",
                valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
                valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            )
        ]
        response = GetMacaroonResponse(macaroons=macaroons)

        assert response.macaroon is None
        assert response.macaroons is not None
        assert len(response.macaroons) == 1

    def test_get_macaroon_rejects_both_fields(self):
        """Test that GetMacaroonResponse rejects having both fields set."""
        macaroons = [
            ExistingMacaroon(
                session_id="session-1",
                valid_since=datetime.datetime(2024, 1, 1, 0, 0, 0),
                valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
            )
        ]

        with pytest.raises(pydantic.ValidationError) as exc_info:
            GetMacaroonResponse(macaroon="bakery-v2-macaroon", macaroons=macaroons)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Cannot have both 'macaroon' and 'macaroons' present" in str(
            errors[0].get("ctx", {}).get("error", "")
        )

    def test_get_macaroon_rejects_neither_field(self):
        """Test that GetMacaroonResponse rejects having neither field set."""
        with pytest.raises(pydantic.ValidationError) as exc_info:
            GetMacaroonResponse()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Either 'macaroon' or 'macaroons' must be present" in str(
            errors[0].get("ctx", {}).get("error", "")
        )

    def test_get_macaroon_unmarshalling_with_macaroon(self):
        """Test unmarshalling JSON with macaroon field."""
        data = {"macaroon": "test-macaroon-string"}
        response = GetMacaroonResponse.unmarshal(data)

        assert response.macaroon == "test-macaroon-string"
        assert response.macaroons is None

    def test_get_macaroon_unmarshalling_with_macaroons(self):
        """Test unmarshalling JSON with macaroons field."""
        data = {
            "macaroons": [
                {
                    "session-id": "session-1",
                    "valid-since": "2024-01-01T00:00:00Z",
                    "valid-until": "2024-12-31T23:59:59Z",
                }
            ]
        }
        response = GetMacaroonResponse.unmarshal(data)

        assert response.macaroon is None
        assert response.macaroons is not None
        assert len(response.macaroons) == 1
        assert response.macaroons[0].session_id == "session-1"
