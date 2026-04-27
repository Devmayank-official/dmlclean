"""
Comprehensive Repository Tests for DMLClean.

Tests for all repository classes to increase coverage.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from dmlclean.storage.history_repo import HistoryRepository
from dmlclean.storage.manifest_repo import ManifestRepository
from dmlclean.storage.protected_repo import ProtectedRepository
from dmlclean.storage.schedule_repo import ScheduleRepository
from dmlclean.storage.trend_repo import TrendRepository


class TestHistoryRepository:
    """Tests for HistoryRepository."""

    def test_create_success(self, db) -> None:
        """Test creating history entry."""
        repo = HistoryRepository(db)

        entry = repo.create(
            id="test-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=10,
            files_deleted=8,
            size_bytes=1024,
            duration_ms=500,
        )

        assert entry.id == "test-id"
        assert entry.mode == "trash"
        assert entry.files_deleted == 8

    def test_create_duplicate(self, db) -> None:
        """Test creating duplicate entry raises error."""
        repo = HistoryRepository(db)

        repo.create(
            id="dup-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        with pytest.raises(Exception):  # DuplicateError
            repo.create(
                id="dup-id",
                mode="trash",
                profile="developer",
                scan_mode="fast",
            )

    def test_get_by_id(self, db) -> None:
        """Test getting entry by ID."""
        repo = HistoryRepository(db)

        repo.create(
            id="get-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        retrieved = repo.get_by_id("get-id")

        assert retrieved is not None
        assert retrieved.id == "get-id"

    def test_get_by_id_not_found(self, db) -> None:
        """Test getting non-existent entry."""
        repo = HistoryRepository(db)

        result = repo.get_by_id("nonexistent")

        assert result is None

    def test_list_all(self, db) -> None:
        """Test listing all entries."""
        repo = HistoryRepository(db)

        # Create multiple entries
        for i in range(5):
            repo.create(
                id=f"list-id-{i}",
                mode="trash",
                profile="developer",
                scan_mode="fast",
            )

        entries = repo.list_all(limit=10)

        assert len(entries) >= 5

    def test_list_with_filters(self, db) -> None:
        """Test listing with filters."""
        repo = HistoryRepository(db)

        repo.create(
            id="filter-id-1",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            status="complete",
        )
        repo.create(
            id="filter-id-2",
            mode="dry-run",
            profile="gamer",
            scan_mode="fast",
            status="complete",
        )

        # Filter by profile
        entries = repo.list_all(limit=10, profile="developer")
        assert len(entries) >= 1

        # Filter by mode
        entries = repo.list_all(limit=10, mode="trash")
        assert len(entries) >= 1

    def test_update(self, db) -> None:
        """Test updating entry."""
        repo = HistoryRepository(db)

        repo.create(
            id="update-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            status="complete",
        )

        result = repo.update("update-id", status="failed", error_message="Test error")

        assert result is True

        updated = repo.get_by_id("update-id")
        assert updated.status == "failed"

    def test_update_nonexistent(self, db) -> None:
        """Test updating non-existent entry."""
        repo = HistoryRepository(db)

        result = repo.update("nonexistent", status="failed")

        assert result is False

    def test_delete(self, db) -> None:
        """Test deleting entry."""
        repo = HistoryRepository(db)

        repo.create(
            id="delete-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        result = repo.delete("delete-id")

        assert result is True
        assert repo.get_by_id("delete-id") is None

    def test_exists(self, db) -> None:
        """Test checking existence."""
        repo = HistoryRepository(db)

        repo.create(
            id="exists-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        assert repo.exists("exists-id") is True
        assert repo.exists("nonexistent") is False

    def test_count(self, db) -> None:
        """Test counting entries."""
        repo = HistoryRepository(db)

        initial_count = repo.count()

        repo.create(
            id="count-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        assert repo.count() == initial_count + 1

    def test_get_summary(self, db) -> None:
        """Test getting summary statistics."""
        repo = HistoryRepository(db)

        repo.create(
            id="summary-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_deleted=10,
            size_bytes=1024,
            duration_ms=500,
            status="complete",
        )

        summary = repo.get_summary(days=30)

        assert summary["total_operations"] >= 1
        assert summary["total_files_deleted"] >= 10

    def test_get_failed(self, db) -> None:
        """Test getting failed entries."""
        repo = HistoryRepository(db)

        repo.create(
            id="failed-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            status="failed",
            error_message="Test error",
        )

        failed = repo.get_failed(limit=10)

        assert len(failed) >= 1

    def test_get_by_profile(self, db) -> None:
        """Test getting entries by profile."""
        repo = HistoryRepository(db)

        repo.create(
            id="profile-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        entries = repo.get_by_profile("developer", limit=10)

        assert len(entries) >= 1

    def test_clear_all(self, db) -> None:
        """Test clearing all entries."""
        repo = HistoryRepository(db)

        repo.create(
            id="clear-id",
            mode="trash",
            profile="developer",
            scan_mode="fast",
        )

        count = repo.clear_all()

        assert count >= 1
        assert repo.count() == 0


class TestScheduleRepository:
    """Tests for ScheduleRepository."""

    def test_create_success(self, db) -> None:
        """Test creating schedule."""
        repo = ScheduleRepository(db)

        entry = repo.create(
            id="schedule-id",
            name="Test Schedule",
            cron_expression="0 3 * * *",
            profile="developer",
            clean_mode="trash",
        )

        assert entry.id == "schedule-id"
        assert entry.name == "Test Schedule"

    def test_create_duplicate(self, db) -> None:
        """Test creating duplicate schedule."""
        repo = ScheduleRepository(db)

        repo.create(
            id="dup-schedule",
            name="Test",
            cron_expression="0 3 * * *",
        )

        with pytest.raises(Exception):  # DuplicateError
            repo.create(
                id="dup-schedule",
                name="Test",
                cron_expression="0 3 * * *",
            )

    def test_get_by_id(self, db) -> None:
        """Test getting schedule by ID."""
        repo = ScheduleRepository(db)

        repo.create(
            id="get-schedule",
            name="Test",
            cron_expression="0 3 * * *",
        )

        retrieved = repo.get_by_id("get-schedule")

        assert retrieved is not None

    def test_list_all(self, db) -> None:
        """Test listing schedules."""
        repo = ScheduleRepository(db)

        for i in range(3):
            repo.create(
                id=f"list-schedule-{i}",
                name=f"Test {i}",
                cron_expression="0 3 * * *",
            )

        entries = repo.list_all(limit=10)

        assert len(entries) >= 3

    def test_update(self, db) -> None:
        """Test updating schedule."""
        repo = ScheduleRepository(db)

        repo.create(
            id="update-schedule",
            name="Test",
            cron_expression="0 3 * * *",
            enabled=True,
        )

        result = repo.update("update-schedule", enabled=False)

        assert result is True

    def test_delete(self, db) -> None:
        """Test deleting schedule."""
        repo = ScheduleRepository(db)

        repo.create(
            id="delete-schedule",
            name="Test",
            cron_expression="0 3 * * *",
        )

        result = repo.delete("delete-schedule")

        assert result is True

    def test_mark_run(self, db) -> None:
        """Test marking schedule run."""
        repo = ScheduleRepository(db)

        repo.create(
            id="run-schedule",
            name="Test",
            cron_expression="0 3 * * *",
        )

        result = repo.mark_run("run-schedule", success=True)

        assert result is True

    def test_get_enabled(self, db) -> None:
        """Test getting enabled schedules."""
        repo = ScheduleRepository(db)

        repo.create(
            id="enabled-schedule",
            name="Test",
            cron_expression="0 3 * * *",
            enabled=True,
        )

        enabled = repo.get_enabled()

        assert len(enabled) >= 1


class TestProtectedRepository:
    """Tests for ProtectedRepository."""

    def test_create_success(self, db) -> None:
        """Test creating protected path."""
        repo = ProtectedRepository(db)

        entry = repo.create(
            id="protect-id",
            path="/test/path",
            description="Test protection",
            is_glob=False,
        )

        assert entry.id == "protect-id"
        assert entry.path == "/test/path"

    def test_create_glob_pattern(self, db) -> None:
        """Test creating glob pattern."""
        repo = ProtectedRepository(db)

        entry = repo.create(
            id="glob-id",
            path="**/*.log",
            description="Log files",
            is_glob=True,
        )

        assert entry.is_glob is True

    def test_create_duplicate(self, db) -> None:
        """Test creating duplicate protection."""
        repo = ProtectedRepository(db)

        repo.create(
            id="dup-protect",
            path="/duplicate",
            description="Test",
        )

        with pytest.raises(Exception):  # DuplicateError
            repo.create(
                id="dup-protect-2",
                path="/duplicate",
                description="Test",
            )

    def test_get_by_path(self, db) -> None:
        """Test getting by path."""
        repo = ProtectedRepository(db)

        repo.create(
            id="path-id",
            path="/get-by-path",
            description="Test",
        )

        entry = repo.get_by_path("/get-by-path")

        assert entry is not None

    def test_list_all(self, db) -> None:
        """Test listing protected paths."""
        repo = ProtectedRepository(db)

        for i in range(3):
            repo.create(
                id=f"list-protect-{i}",
                path=f"/test/{i}",
                description="Test",
            )

        entries = repo.list_all(limit=10)

        assert len(entries) >= 3

    def test_update(self, db) -> None:
        """Test updating protected path."""
        repo = ProtectedRepository(db)

        repo.create(
            id="update-protect",
            path="/test",
            description="Original",
        )

        result = repo.update("update-protect", description="Updated")

        assert result is True

    def test_delete(self, db) -> None:
        """Test deleting protected path."""
        repo = ProtectedRepository(db)

        repo.create(
            id="delete-protect",
            path="/test",
            description="Test",
        )

        result = repo.delete("delete-protect")

        assert result is True

    def test_exists_by_path(self, db) -> None:
        """Test checking existence by path."""
        repo = ProtectedRepository(db)

        repo.create(
            id="exists-protect",
            path="/exists",
            description="Test",
        )

        assert repo.exists_by_path("/exists") is True


class TestManifestRepository:
    """Tests for ManifestRepository."""

    def test_create_success(self, db) -> None:
        """Test creating manifest."""
        repo = ManifestRepository(db)

        entry = repo.create(
            id="manifest-id",
            manifest_path="/test/manifest.json",
            created_at=datetime.now().isoformat(),
            file_count=10,
            size_bytes=1024,
        )

        assert entry.id == "manifest-id"
        assert entry.file_count == 10

    def test_mark_undone(self, db) -> None:
        """Test marking manifest as undone."""
        repo = ManifestRepository(db)

        repo.create(
            id="undo-manifest",
            manifest_path="/test.json",
            created_at=datetime.now().isoformat(),
        )

        result = repo.mark_undone("undo-manifest")

        assert result is True

    def test_list_undone(self, db) -> None:
        """Test listing undone manifests."""
        repo = ManifestRepository(db)

        repo.create(
            id="undone-manifest",
            manifest_path="/test.json",
            created_at=datetime.now().isoformat(),
        )
        repo.mark_undone("undone-manifest")

        undone = repo.list_undone(limit=10)

        assert len(undone) >= 1


class TestTrendRepository:
    """Tests for TrendRepository."""

    def test_create_success(self, db) -> None:
        """Test creating trend entry."""
        repo = TrendRepository(db)

        entry = repo.create(
            id="trend-id",
            mount_point="/",
            total_bytes=1024 * 1024 * 1024,
            used_bytes=1024 * 1024 * 512,
            free_bytes=1024 * 1024 * 512,
        )

        assert entry.id == "trend-id"
        assert entry.mount_point == "/"

    def test_get_summary(self, db) -> None:
        """Test getting trend summary."""
        repo = TrendRepository(db)

        repo.create(
            id="summary-trend",
            mount_point="/",
            total_bytes=1024 * 1024 * 1024,
            used_bytes=1024 * 1024 * 512,
            free_bytes=1024 * 1024 * 512,
        )

        summary = repo.get_summary(days=30)

        assert "total_entries" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
