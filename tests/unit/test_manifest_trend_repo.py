# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ManifestRepository and TrendRepository."""

from __future__ import annotations

import pytest

from dmlclean.exceptions.repository import DataError, DuplicateError
from dmlclean.storage.database import Database
from dmlclean.storage.manifest_repo import ManifestRepository
from dmlclean.storage.trend_repo import TrendRepository

# ============== ManifestRepository Tests ==============


class TestManifestRepositoryCreate:
    """Tests for ManifestRepository.create()"""

    def test_create_success(self, db: Database) -> None:
        """Test successful manifest creation."""
        repo = ManifestRepository(db)
        record = repo.create(
            id="manifest-001",
            manifest_path="/path/to/manifest.json",
            created_at="2026-03-11T00:00:00Z",
            file_count=100,
            size_bytes=1024 * 1024 * 50,
        )
        assert record.id == "manifest-001"
        assert record.file_count == 100

    def test_create_duplicate_raises_error(self, db: Database) -> None:
        """Test duplicate creation raises error."""
        repo = ManifestRepository(db)
        repo.create(
            id="manifest-002",
            manifest_path="/path/to/manifest.json",
            created_at="2026-03-11T00:00:00Z",
        )
        with pytest.raises(DuplicateError):
            repo.create(
                id="manifest-002",
                manifest_path="/path/to/manifest2.json",
                created_at="2026-03-11T00:00:00Z",
            )

    def test_create_empty_id_raises_error(self, db: Database) -> None:
        """Test empty ID raises error."""
        repo = ManifestRepository(db)
        with pytest.raises(DataError, match="ID cannot be empty"):
            repo.create(
                id="", manifest_path="/path/to/manifest.json", created_at="2026-03-11T00:00:00Z"
            )

    def test_create_empty_path_raises_error(self, db: Database) -> None:
        """Test empty path raises error."""
        repo = ManifestRepository(db)
        with pytest.raises(DataError, match="manifest_path cannot be empty"):
            repo.create(id="manifest-003", manifest_path="", created_at="2026-03-11T00:00:00Z")


class TestManifestRepositoryGet:
    """Tests for ManifestRepository.get_by_id()"""

    def test_get_existing(self, db: Database) -> None:
        """Test getting existing entry."""
        repo = ManifestRepository(db)
        repo.create(
            id="manifest-004",
            manifest_path="/path/to/manifest.json",
            created_at="2026-03-11T00:00:00Z",
        )
        record = repo.get_by_id("manifest-004")
        assert record is not None
        assert record.id == "manifest-004"

    def test_get_nonexistent(self, db: Database) -> None:
        """Test getting non-existent entry."""
        repo = ManifestRepository(db)
        record = repo.get_by_id("nonexistent")
        assert record is None


class TestManifestRepositoryUpdate:
    """Tests for ManifestRepository.update()"""

    def test_update_success(self, db: Database) -> None:
        """Test successful update."""
        repo = ManifestRepository(db)
        repo.create(
            id="manifest-005",
            manifest_path="/path/to/manifest.json",
            created_at="2026-03-11T00:00:00Z",
        )
        result = repo.update("manifest-005", file_count=150)
        assert result is True
        record = repo.get_by_id("manifest-005")
        assert record is not None
        assert record.file_count == 150

    def test_update_nonexistent(self, db: Database) -> None:
        """Test updating non-existent entry."""
        repo = ManifestRepository(db)
        result = repo.update("nonexistent", file_count=150)
        assert result is False


class TestManifestRepositoryDelete:
    """Tests for ManifestRepository.delete()"""

    def test_delete_success(self, db: Database) -> None:
        """Test successful deletion."""
        repo = ManifestRepository(db)
        repo.create(
            id="manifest-006",
            manifest_path="/path/to/manifest.json",
            created_at="2026-03-11T00:00:00Z",
        )
        result = repo.delete("manifest-006")
        assert result is True
        assert repo.get_by_id("manifest-006") is None


class TestManifestRepositoryMarkUndone:
    """Tests for ManifestRepository.mark_undone()"""

    def test_mark_undone_success(self, db: Database) -> None:
        """Test marking as undone."""
        repo = ManifestRepository(db)
        repo.create(
            id="manifest-007",
            manifest_path="/path/to/manifest.json",
            created_at="2026-03-11T00:00:00Z",
        )
        result = repo.mark_undone("manifest-007")
        assert result is True
        record = repo.get_by_id("manifest-007")
        assert record is not None
        assert record.undone is True


class TestManifestRepositoryListUndone:
    """Tests for ManifestRepository.list_undone()"""

    def test_list_undone(self, db: Database) -> None:
        """Test listing undone manifests."""
        repo = ManifestRepository(db)
        repo.create(
            id="manifest-008",
            manifest_path="/path/to/manifest1.json",
            created_at="2026-03-11T00:00:00Z",
        )
        repo.create(
            id="manifest-009",
            manifest_path="/path/to/manifest2.json",
            created_at="2026-03-11T00:00:00Z",
        )
        repo.mark_undone("manifest-009")
        undone = repo.list_undone()
        assert len(undone) == 1
        assert undone[0].undone is True


# ============== TrendRepository Tests ==============


class TestTrendRepositoryCreate:
    """Tests for TrendRepository.create()"""

    def test_create_success(self, db: Database) -> None:
        """Test successful trend entry creation."""
        repo = TrendRepository(db)
        entry = repo.create(
            mount_point="C:\\",
            total_bytes=1024 * 1024 * 1024 * 500,
            free_bytes=1024 * 1024 * 1024 * 200,
        )
        assert entry.mount_point == "C:\\"
        assert entry.total_bytes == 1024 * 1024 * 1024 * 500
        assert entry.used_bytes == 1024 * 1024 * 1024 * 300

    def test_create_empty_mount_point_raises_error(self, db: Database) -> None:
        """Test empty mount point raises error."""
        repo = TrendRepository(db)
        with pytest.raises(DataError, match="Mount point cannot be empty"):
            repo.create(mount_point="", total_bytes=100, free_bytes=50)

    def test_create_negative_bytes_raises_error(self, db: Database) -> None:
        """Test negative bytes raises error."""
        repo = TrendRepository(db)
        with pytest.raises(DataError, match="cannot be negative"):
            repo.create(mount_point="C:\\", total_bytes=-100, free_bytes=50)


class TestTrendRepositoryGet:
    """Tests for TrendRepository.get_by_id()"""

    def test_get_existing(self, db: Database) -> None:
        """Test getting existing entry."""
        repo = TrendRepository(db)
        repo.create(mount_point="C:\\", total_bytes=500, free_bytes=200)
        entry = repo.get_by_id(1)
        assert entry is not None
        assert entry.mount_point == "C:\\"

    def test_get_nonexistent(self, db: Database) -> None:
        """Test getting non-existent entry."""
        repo = TrendRepository(db)
        entry = repo.get_by_id(999)
        assert entry is None


class TestTrendRepositoryList:
    """Tests for TrendRepository.list_all()"""

    def test_list_empty(self, db: Database) -> None:
        """Test listing when empty."""
        repo = TrendRepository(db)
        entries = repo.list_all()
        assert len(entries) == 0

    def test_list_with_entries(self, db: Database) -> None:
        """Test listing with entries."""
        repo = TrendRepository(db)
        repo.create(mount_point="C:\\", total_bytes=500, free_bytes=200)
        repo.create(mount_point="/", total_bytes=1000, free_bytes=400)
        entries = repo.list_all()
        assert len(entries) == 2

    def test_list_by_mount_point(self, db: Database) -> None:
        """Test filtering by mount point."""
        repo = TrendRepository(db)
        repo.create(mount_point="C:\\", total_bytes=500, free_bytes=200)
        repo.create(mount_point="/", total_bytes=1000, free_bytes=400)
        entries = repo.list_all(mount_point="C:\\")
        assert len(entries) == 1
        assert entries[0].mount_point == "C:\\"


class TestTrendRepositoryCount:
    """Tests for TrendRepository.count()"""

    def test_count_empty(self, db: Database) -> None:
        """Test count when empty."""
        repo = TrendRepository(db)
        assert repo.count() == 0

    def test_count_with_entries(self, db: Database) -> None:
        """Test count with entries."""
        repo = TrendRepository(db)
        repo.create(mount_point="C:\\", total_bytes=500, free_bytes=200)
        repo.create(mount_point="/", total_bytes=1000, free_bytes=400)
        assert repo.count() == 2


class TestTrendRepositoryGetSummary:
    """Tests for TrendRepository.get_summary()"""

    def test_get_summary_empty(self, db: Database) -> None:
        """Test summary when empty."""
        repo = TrendRepository(db)
        summary = repo.get_summary(days=30)
        assert summary["total_entries"] == 0

    def test_get_summary_with_entries(self, db: Database) -> None:
        """Test summary with entries."""
        repo = TrendRepository(db)
        repo.create(mount_point="C:\\", total_bytes=500, free_bytes=200)
        summary = repo.get_summary(days=30)
        assert summary["total_entries"] == 1


class TestTrendRepositoryClearOld:
    """Tests for TrendRepository.clear_old()"""

    def test_clear_old_success(self, db: Database) -> None:
        """Test clearing old entries."""
        repo = TrendRepository(db)
        repo.create(mount_point="C:\\", total_bytes=500, free_bytes=200)
        count = repo.clear_old(days=90)
        # Entry is new, so shouldn't be cleared
        assert count == 0
