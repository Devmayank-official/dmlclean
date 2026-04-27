# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for history service.

Comprehensive test coverage for HistoryService.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from dmlclean.exceptions import NotFoundError
from dmlclean.services.history_service import HistoryService


class TestHistoryService:
    """Test history service."""

    def test_init(self, db, history_repo, undo_manager) -> None:
        """Test service initialization."""
        service = HistoryService(db, history_repo, undo_manager)
        assert service.db == db
        assert service.history_repo == history_repo
        assert service.undo_manager == undo_manager

    def test_list_recent(self, history_service, history_repo) -> None:
        """Test listing recent history."""
        history_service.list_recent(limit=10, profile="developer")
        history_repo.list_all.assert_called_once_with(
            limit=10, profile="developer", status=None, mode=None
        )

    def test_get_entry(self, history_service, history_repo) -> None:
        """Test getting history entry."""
        history_service.get_entry("test-id")
        history_repo.get_by_id.assert_called_once_with("test-id")

    def test_get_entry_or_raise_not_found(self, history_service, history_repo) -> None:
        """Test get entry raises NotFoundError."""
        history_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            history_service.get_entry_or_raise("nonexistent-id")

    def test_clear_history(self, history_service, history_repo, undo_manager) -> None:
        """Test clearing history."""
        history_repo.clear_all.return_value = 5
        undo_manager.clear_history = Mock()

        result = history_service.clear_history()

        assert result == 5
        undo_manager.clear_history.assert_called_once()
        history_repo.clear_all.assert_called_once()

    def test_get_statistics(self, history_service, history_repo) -> None:
        """Test getting statistics."""
        history_repo.get_summary.return_value = {
            "total_operations": 10,
            "total_files_deleted": 500,
            "total_size_bytes": 1024000,
            "avg_duration_ms": 1500,
        }

        stats = history_service.get_statistics(days=30)

        assert stats["total_operations"] == 10
        history_repo.get_summary.assert_called_once_with(days=30)

    def test_export_history(self, history_service, undo_manager) -> None:
        """Test exporting history."""
        output_path = Path("/tmp/history.json")
        undo_manager.export_history.return_value = 10

        result = history_service.export_history(output_path)

        assert result == 10
        undo_manager.export_history.assert_called_once_with(output_path)


__all__ = ["TestHistoryService"]
