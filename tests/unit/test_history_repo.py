# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for HistoryRepository.

Tests cover all CRUD operations and edge cases.
"""

from __future__ import annotations

import pytest

from dmlclean.exceptions.repository import DataError, DuplicateError
from dmlclean.storage.database import Database
from dmlclean.storage.history_repo import HistoryRepository


@pytest.fixture
def repo(db: Database) -> HistoryRepository:
    """Create a HistoryRepository instance."""
    return HistoryRepository(db)


class TestHistoryRepositoryCreate:
    """Tests for HistoryRepository.create()"""

    def test_create_success(self, repo: HistoryRepository) -> None:
        """Test successful history entry creation."""
        entry = repo.create(
            id="test-001",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=100,
            files_deleted=95,
            size_bytes=1024 * 1024 * 50,
            duration_ms=2500,
        )

        assert entry.id == "test-001"
        assert entry.mode == "trash"
        assert entry.files_deleted == 95
        assert entry.status == "complete"

    def test_create_duplicate_raises_error(self, repo: HistoryRepository) -> None:
        """Test that creating duplicate entry raises DuplicateError."""
        repo.create(
            id="test-002",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        with pytest.raises(DuplicateError):
            repo.create(
                id="test-002",
                mode="trash",
                profile="developer",
                scan_mode="fast",
            )

    def test_create_empty_id_raises_error(self, repo: HistoryRepository) -> None:
        """Test that empty ID raises DataError."""
        with pytest.raises(DataError, match="ID cannot be empty"):
            repo.create(
                id="",
                mode="trash",
                profile="developer",
                scan_mode="fast",
            )

    def test_create_empty_mode_raises_error(self, repo: HistoryRepository) -> None:
        """Test that empty mode raises DataError."""
        with pytest.raises(DataError, match="Mode cannot be empty"):
            repo.create(
                id="test-003",
                mode="",
                profile="developer",
                scan_mode="fast",
            )

    def test_create_invalid_mode_raises_error(self, repo: HistoryRepository) -> None:
        """Test that invalid mode raises DataError."""
        with pytest.raises(DataError, match="Invalid mode"):
            repo.create(
                id="test-004",
                mode="invalid-mode",
                profile="developer",
                scan_mode="fast",
            )


class TestHistoryRepositoryGet:
    """Tests for HistoryRepository.get_by_id()"""

    def test_get_existing_entry(self, repo: HistoryRepository) -> None:
        """Test getting an existing entry."""
        repo.create(
            id="test-005",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        entry = repo.get_by_id("test-005")
        assert entry is not None
        assert entry.id == "test-005"
        assert entry.mode == "trash"

    def test_get_nonexistent_entry(self, repo: HistoryRepository) -> None:
        """Test getting a non-existent entry returns None."""
        entry = repo.get_by_id("nonexistent")
        assert entry is None


class TestHistoryRepositoryList:
    """Tests for HistoryRepository.list_all()"""

    def test_list_all_empty(self, repo: HistoryRepository) -> None:
        """Test listing when no entries exist."""
        entries = repo.list_all()
        assert len(entries) == 0

    def test_list_all_with_entries(self, repo: HistoryRepository) -> None:
        """Test listing with multiple entries."""
        repo.create(id="test-006", mode="trash", profile="developer", scan_mode="fast")
        repo.create(id="test-007", mode="permanent", profile="developer", scan_mode="fast")
        repo.create(id="test-008", mode="dry-run", profile="system-admin", scan_mode="deep")

        entries = repo.list_all()
        assert len(entries) == 3

    def test_list_with_limit(self, repo: HistoryRepository) -> None:
        """Test listing with limit."""
        for i in range(10):
            repo.create(id=f"test-{i:03d}", mode="trash", profile="developer", scan_mode="fast")

        entries = repo.list_all(limit=5)
        assert len(entries) == 5

    def test_list_with_profile_filter(self, repo: HistoryRepository) -> None:
        """Test listing with profile filter."""
        repo.create(id="test-009", mode="trash", profile="developer", scan_mode="fast")
        repo.create(id="test-010", mode="trash", profile="system-admin", scan_mode="fast")

        entries = repo.list_all(profile="developer")
        assert len(entries) == 1
        assert entries[0].profile == "developer"

    def test_list_with_status_filter(self, repo: HistoryRepository) -> None:
        """Test listing with status filter."""
        repo.create(id="test-011", mode="trash", profile="developer", scan_mode="fast")
        entry2 = repo.create(
            id="test-012",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            status="failed",
            error_message="Test error",
        )

        entries = repo.list_all(status="failed")
        assert len(entries) == 1
        assert entries[0].id == entry2.id


class TestHistoryRepositoryUpdate:
    """Tests for HistoryRepository.update()"""

    def test_update_success(self, repo: HistoryRepository) -> None:
        """Test successful update."""
        repo.create(id="test-013", mode="trash", profile="developer", scan_mode="fast")

        result = repo.update("test-013", status="failed", error_message="Test error")
        assert result is True

        entry = repo.get_by_id("test-013")
        assert entry is not None
        assert entry.status == "failed"
        assert entry.error_message == "Test error"

    def test_update_nonexistent_entry(self, repo: HistoryRepository) -> None:
        """Test updating non-existent entry returns False."""
        result = repo.update("nonexistent", status="failed")
        assert result is False

    def test_update_no_fields_raises_error(self, repo: HistoryRepository) -> None:
        """Test updating with no fields raises DataError."""
        repo.create(id="test-014", mode="trash", profile="developer", scan_mode="fast")

        with pytest.raises(DataError, match="No valid fields"):
            repo.update("test-014", invalid_field="value")


class TestHistoryRepositoryDelete:
    """Tests for HistoryRepository.delete()"""

    def test_delete_success(self, repo: HistoryRepository) -> None:
        """Test successful deletion."""
        repo.create(id="test-015", mode="trash", profile="developer", scan_mode="fast")

        result = repo.delete("test-015")
        assert result is True
        assert repo.get_by_id("test-015") is None

    def test_delete_nonexistent_entry(self, repo: HistoryRepository) -> None:
        """Test deleting non-existent entry returns False."""
        result = repo.delete("nonexistent")
        assert result is False


class TestHistoryRepositoryExists:
    """Tests for HistoryRepository.exists()"""

    def test_exists_true(self, repo: HistoryRepository) -> None:
        """Test exists returns True for existing entry."""
        repo.create(id="test-016", mode="trash", profile="developer", scan_mode="fast")
        assert repo.exists("test-016") is True

    def test_exists_false(self, repo: HistoryRepository) -> None:
        """Test exists returns False for non-existent entry."""
        assert repo.exists("nonexistent") is False


class TestHistoryRepositoryCount:
    """Tests for HistoryRepository.count()"""

    def test_count_empty(self, repo: HistoryRepository) -> None:
        """Test count with no entries."""
        assert repo.count() == 0

    def test_count_with_entries(self, repo: HistoryRepository) -> None:
        """Test count with multiple entries."""
        repo.create(id="test-017", mode="trash", profile="developer", scan_mode="fast")
        repo.create(id="test-018", mode="trash", profile="developer", scan_mode="fast")
        repo.create(id="test-019", mode="trash", profile="developer", scan_mode="fast")

        assert repo.count() == 3


class TestHistoryRepositoryGetSummary:
    """Tests for HistoryRepository.get_summary()"""

    def test_get_summary_empty(self, repo: HistoryRepository) -> None:
        """Test summary with no entries."""
        summary = repo.get_summary(days=30)

        assert summary["total_operations"] == 0
        assert summary["total_files_deleted"] == 0

    def test_get_summary_with_entries(self, repo: HistoryRepository) -> None:
        """Test summary with entries."""
        repo.create(
            id="test-020",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=100,
            files_deleted=95,
            size_bytes=1024 * 1024 * 50,
            duration_ms=2500,
        )

        summary = repo.get_summary(days=30)

        assert summary["total_operations"] == 1
        assert summary["total_files_deleted"] == 95
        assert summary["successful"] == 1


class TestHistoryRepositoryClearAll:
    """Tests for HistoryRepository.clear_all()"""

    def test_clear_all_success(self, repo: HistoryRepository) -> None:
        """Test clearing all entries."""
        repo.create(id="test-021", mode="trash", profile="developer", scan_mode="fast")
        repo.create(id="test-022", mode="trash", profile="developer", scan_mode="fast")
        repo.create(id="test-023", mode="trash", profile="developer", scan_mode="fast")

        count = repo.clear_all()
        assert count == 3
        assert repo.count() == 0


class TestHistoryRepositoryGetFailed:
    """Tests for HistoryRepository.get_failed()"""

    def test_get_failed_empty(self, repo: HistoryRepository) -> None:
        """Test getting failed entries when none exist."""
        failed = repo.get_failed(limit=10)
        assert len(failed) == 0

    def test_get_failed_with_entries(self, repo: HistoryRepository) -> None:
        """Test getting failed entries."""
        repo.create(
            id="test-024", mode="trash", profile="developer", scan_mode="fast", status="complete"
        )
        repo.create(
            id="test-025",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            status="failed",
            error_message="Test error",
        )

        failed = repo.get_failed(limit=10)
        assert len(failed) == 1
        assert failed[0].id == "test-025"
        assert failed[0].status == "failed"


class TestHistoryRepositoryGetByProfile:
    """Tests for HistoryRepository.get_by_profile()"""

    def test_get_by_profile_empty(self, repo: HistoryRepository) -> None:
        """Test getting by profile when none exist."""
        entries = repo.get_by_profile("developer")
        assert len(entries) == 0

    def test_get_by_profile_with_entries(self, repo: HistoryRepository) -> None:
        """Test getting entries by profile."""
        repo.create(id="test-026", mode="trash", profile="developer", scan_mode="fast")
        repo.create(id="test-027", mode="trash", profile="system-admin", scan_mode="fast")
        repo.create(id="test-028", mode="trash", profile="developer", scan_mode="fast")

        entries = repo.get_by_profile("developer")
        assert len(entries) == 2
        assert all(e.profile == "developer" for e in entries)
