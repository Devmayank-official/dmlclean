# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for protection service.

Comprehensive test coverage for ProtectionService.
"""

from unittest.mock import Mock

import pytest

from dmlclean.exceptions import DuplicateError, NotFoundError, PermissionError, ValidationError
from dmlclean.services.protection_service import ProtectionService


class TestProtectionService:
    """Test protection service."""

    def test_init(self, db, protected_repo, protected_zone) -> None:
        """Test service initialization."""
        service = ProtectionService(db, protected_repo, protected_zone)
        assert service.db == db
        assert service.protected_repo == protected_repo
        assert service.protected_zone == protected_zone

    def test_add_protection_empty_path_raises(self, protection_service) -> None:
        """Test adding empty path raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            protection_service.add_protection("")

    def test_add_protection_too_long_raises(self, protection_service) -> None:
        """Test adding too long path raises ValidationError."""
        with pytest.raises(ValidationError, match="too long"):
            protection_service.add_protection("a" * 600)

    def test_add_protection_duplicate_raises(self, protection_service, protected_repo) -> None:
        """Test adding duplicate path raises DuplicateError."""
        mock_entry = Mock()
        protected_repo.get_by_path.return_value = mock_entry

        with pytest.raises(DuplicateError):
            protection_service.add_protection("/duplicate/path")

    def test_add_protection_immutable_raises(self, protection_service) -> None:
        """Test adding immutable system path raises PermissionError."""
        with pytest.raises(PermissionError, match="immutable"):
            protection_service.add_protection("C:\\Windows\\System32")

    def test_add_protection_success(self, protection_service, protected_repo, event_bus) -> None:
        """Test successfully adding protected path."""
        protected_repo.get_by_path.return_value = None
        protected_repo.create.return_value = Mock(id="test-id", path="/test/path")

        entry = protection_service.add_protection("/test/path", "Test description")

        assert entry is not None
        protected_repo.create.assert_called_once()

    def test_remove_protection_not_found(self, protection_service, protected_repo) -> None:
        """Test removing non-existent protection raises NotFoundError."""
        protected_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            protection_service.remove_protection("nonexistent-id")

    def test_remove_protection_success(self, protection_service, protected_repo, event_bus) -> None:
        """Test successfully removing protected path."""
        mock_entry = Mock(id="test-id", path="/test/path")
        protected_repo.get_by_id.return_value = mock_entry
        protected_repo.delete.return_value = True

        result = protection_service.remove_protection("test-id")

        assert result is True
        protected_repo.delete.assert_called_once_with("test-id")

    def test_list_protected(self, protection_service, protected_repo) -> None:
        """Test listing protected paths."""
        protection_service.list_protected(limit=50, is_glob=False)
        protected_repo.list_all.assert_called_once_with(limit=50, is_glob=False)

    def test_check_protection(self, protection_service, protected_zone) -> None:
        """Test checking if path is protected."""
        mock_result = Mock(is_protected=True, reason="Test reason")
        protected_zone.is_protected.return_value = mock_result

        result = protection_service.check_protection("/test/path")

        assert result.is_protected is True
        protected_zone.is_protected.assert_called_once()

    def test_is_protected(self, protection_service) -> None:
        """Test boolean protection check."""
        protection_service.check_protection = Mock(return_value=Mock(is_protected=True))

        result = protection_service.is_protected("/test/path")

        assert result is True


__all__ = ["TestProtectionService"]
