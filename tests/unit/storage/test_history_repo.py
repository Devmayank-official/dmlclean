# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for history repository.

Comprehensive test coverage for HistoryRepository.
"""

import pytest


class TestHistoryRepository:
    """Test history repository."""

    def test_create_success(self, history_repo) -> None:
        """Test creating history entry."""
        entry = history_repo.create(
            id="test-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=100,
            files_deleted=95,
            size_bytes=1024000,
            duration_ms=1500,
            categories=["browser", "dev_python"],
            status="complete",
        )

        assert entry.id == "test-id"
        assert entry.mode == "trash"
        assert entry.files_deleted == 95

    def test_create_duplicate_raises(self, history_repo) -> None:
        """Test creating duplicate entry raises DuplicateError."""
        # Create first entry
        history_repo.create(id="dup-id", mode="trash", profile="developer", scan_mode="fast")

        # Try to create duplicate
        with pytest.raises(Exception):  # DuplicateError
            history_repo.create(id="dup-id", mode="trash", profile="developer", scan_mode="fast")

    def test_get_by_id_found(self, history_repo) -> None:
        """Test getting entry by ID."""
        history_repo.create(id="get-id", mode="trash", profile="developer", scan_mode="fast")

        entry = history_repo.get_by_id("get-id")

        assert entry is not None
        assert entry.id == "get-id"

    def test_get_by_id_not_found(self, history_repo) -> None:
        """Test getting non-existent entry."""
        entry = history_repo.get_by_id("nonexistent-id")
        assert entry is None

    def test_list_all(self, history_repo) -> None:
        """Test listing all entries."""
        # Create multiple entries
        for i in range(5):
            history_repo.create(
                id=f"list-id-{i}", mode="trash", profile="developer", scan_mode="fast"
            )

        entries = history_repo.list_all(limit=10)

        assert len(entries) >= 5

    def test_list_all_with_filters(self, history_repo) -> None:
        """Test listing with filters."""
        history_repo.create(
            id="filter-id-1", mode="trash", profile="developer", scan_mode="fast", status="complete"
        )
        history_repo.create(
            id="filter-id-2",
            mode="permanent",
            profile="developer",
            scan_mode="fast",
            status="complete",
        )

        # Filter by mode
        entries = history_repo.list_all(limit=10, mode="trash")

        assert len(entries) >= 1

    def test_update_success(self, history_repo) -> None:
        """Test updating entry."""
        history_repo.create(id="update-id", mode="trash", profile="developer", scan_mode="fast")

        result = history_repo.update("update-id", status="failed", error_message="Test error")

        assert result is True

        entry = history_repo.get_by_id("update-id")
        assert entry.status == "failed"

    def test_update_not_found(self, history_repo) -> None:
        """Test updating non-existent entry."""
        result = history_repo.update("nonexistent-id", status="failed")
        assert result is False

    def test_delete_success(self, history_repo) -> None:
        """Test deleting entry."""
        history_repo.create(id="delete-id", mode="trash", profile="developer", scan_mode="fast")

        result = history_repo.delete("delete-id")

        assert result is True
        assert history_repo.get_by_id("delete-id") is None

    def test_delete_not_found(self, history_repo) -> None:
        """Test deleting non-existent entry."""
        result = history_repo.delete("nonexistent-id")
        assert result is False

    def test_exists(self, history_repo) -> None:
        """Test checking if entry exists."""
        history_repo.create(id="exists-id", mode="trash", profile="developer", scan_mode="fast")

        assert history_repo.exists("exists-id") is True
        assert history_repo.exists("nonexistent-id") is False

    def test_count(self, history_repo) -> None:
        """Test counting entries."""
        initial_count = history_repo.count()

        history_repo.create(id="count-id", mode="trash", profile="developer", scan_mode="fast")

        assert history_repo.count() == initial_count + 1

    def test_get_summary(self, history_repo) -> None:
        """Test getting summary statistics."""
        history_repo.create(
            id="summary-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=100,
            files_deleted=95,
            size_bytes=1024000,
            duration_ms=1500,
        )

        summary = history_repo.get_summary(days=30)

        assert "total_operations" in summary
        assert "total_files_deleted" in summary
        assert "total_size_bytes" in summary

    def test_clear_all(self, history_repo) -> None:
        """Test clearing all entries."""
        history_repo.create(id="clear-id", mode="trash", profile="developer", scan_mode="fast")

        count = history_repo.clear_all()

        assert count >= 1
        assert history_repo.count() == 0


__all__ = ["TestHistoryRepository"]
