"""
Unit tests for DMLClean undo manager.

Uses pyfakefs for fake filesystem.
"""

# ruff: noqa: S108  # reason: test file using pyfakefs - no real disk access

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.safety.manifest import DeletionManifest, ManifestEntry
from dmlclean.safety.undo import UndoManager, UndoUnavailableError


class TestUndoManagerInit:
    """Tests for UndoManager initialization."""

    def test_undo_manager_init_default(self) -> None:
        """Test UndoManager initializes with default storage dir."""
        manager = UndoManager()

        assert manager.storage_dir is not None
        # Updated for new unified path: ~/DML Labs/DML Clean/
        assert "dml labs" in str(manager.storage_dir).lower()
        assert "dml clean" in str(manager.storage_dir).lower()

    def test_undo_manager_init_custom_dir(self, fs: FakeFilesystem) -> None:
        """Test UndoManager initializes with custom storage dir."""
        custom_dir = Path("/custom/storage")
        fs.create_dir(custom_dir)
        manager = UndoManager(storage_dir=custom_dir)

        assert manager.storage_dir == custom_dir


class TestUndoManagerListManifests:
    """Tests for UndoManager.list_manifests."""

    def test_list_manifests_empty(self, fs: FakeFilesystem) -> None:
        """Test list_manifests when no manifests exist."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        manifests = manager.list_manifests()

        assert manifests == []

    def test_list_manifests_with_files(self, fs: FakeFilesystem) -> None:
        """Test list_manifests with manifest files."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manifest1 = DeletionManifest(
            id="test123",
            mode="trash",
            total_files=10,
            total_size_bytes=1024 * 100,
        )
        manifest2 = DeletionManifest(
            id="test456",
            mode="trash",
            total_files=5,
            total_size_bytes=1024 * 50,
        )

        manifest1.save(storage_dir)
        manifest2.save(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        manifests = manager.list_manifests()

        assert len(manifests) == 2

    def test_list_manifests_limit(self, fs: FakeFilesystem) -> None:
        """Test list_manifests respects limit."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        for i in range(5):
            manifest = DeletionManifest(
                id=f"test{i:03d}",
                mode="trash",
                total_files=10,
                total_size_bytes=1024 * 100,
            )
            manifest.save(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        manifests = manager.list_manifests(limit=3)

        assert len(manifests) == 3

    def test_list_manifests_storage_not_exists(self) -> None:
        """Test list_manifests when storage dir doesn't exist."""
        manager = UndoManager(storage_dir=Path("/nonexistent/path"))
        manifests = manager.list_manifests()

        assert manifests == []


class TestUndoManagerGetManifest:
    """Tests for UndoManager.get_manifest."""

    def test_get_manifest_found(self, fs: FakeFilesystem) -> None:
        """Test get_manifest finds manifest by ID."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manifest = DeletionManifest(id="abc123def456", mode="trash")
        manifest.save(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        result = manager.get_manifest("abc123")

        assert result is not None
        assert result.id == "abc123def456"

    def test_get_manifest_partial_id(self, fs: FakeFilesystem) -> None:
        """Test get_manifest with partial ID."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manifest = DeletionManifest(id="abc123def456", mode="trash")
        manifest.save(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        result = manager.get_manifest("abc")

        assert result is not None

    def test_get_manifest_not_found(self, fs: FakeFilesystem) -> None:
        """Test get_manifest returns None when not found."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manifest = DeletionManifest(id="abc123", mode="trash")
        manifest.save(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        result = manager.get_manifest("nonexistent")

        assert result is None


class TestUndoManagerGetLatest:
    """Tests for UndoManager.get_latest_manifest."""

    def test_get_latest_manifest_found(self, fs: FakeFilesystem) -> None:
        """Test get_latest_manifest returns most recent."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manifest1 = DeletionManifest(id="old123", mode="trash")
        manifest2 = DeletionManifest(id="new456", mode="trash")

        manifest1.save(storage_dir)
        manifest2.save(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        result = manager.get_latest_manifest()

        assert result is not None

    def test_get_latest_manifest_empty(self, fs: FakeFilesystem) -> None:
        """Test get_latest_manifest when no manifests."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        result = manager.get_latest_manifest()

        assert result is None


class TestUndoManagerCanUndo:
    """Tests for UndoManager.can_undo."""

    def test_can_undo_permanent_mode(self) -> None:
        """Test can_undo returns False for permanent mode."""
        manifest = DeletionManifest(id="test123", mode="permanent")
        manifest.add_entry(ManifestEntry(path="/test/file.txt", size_bytes=100))

        manager = UndoManager()
        can_undo, reason = manager.can_undo(manifest)

        assert can_undo is False
        assert "Permanent" in reason

    def test_can_undo_dry_run_mode(self) -> None:
        """Test can_undo returns False for dry-run mode."""
        manifest = DeletionManifest(id="test123", mode="dry-run")
        manifest.add_entry(ManifestEntry(path="/test/file.txt", size_bytes=100))

        manager = UndoManager()
        can_undo, reason = manager.can_undo(manifest)

        assert can_undo is False
        assert "Dry-run" in reason

    def test_can_undo_no_entries(self) -> None:
        """Test can_undo returns False for empty manifest."""
        manifest = DeletionManifest(id="test123", mode="trash")

        manager = UndoManager()
        can_undo, reason = manager.can_undo(manifest)

        assert can_undo is False
        assert "no entries" in reason.lower()


class TestUndoManagerUndo:
    """Tests for UndoManager.undo."""

    def test_undo_permanent_raises_error(self) -> None:
        """Test undo raises error for permanent mode."""
        manifest = DeletionManifest(id="test123", mode="permanent")
        manifest.add_entry(ManifestEntry(path="/test/file.txt", size_bytes=100))

        manager = UndoManager()

        with pytest.raises(UndoUnavailableError):
            manager.undo(manifest)

    def test_undo_dry_run_raises_error(self) -> None:
        """Test undo raises error for dry-run mode."""
        manifest = DeletionManifest(id="test123", mode="dry-run")
        manifest.add_entry(ManifestEntry(path="/test/file.txt", size_bytes=100))

        manager = UndoManager()

        with pytest.raises(UndoUnavailableError):
            manager.undo(manifest)

    def test_undo_empty_entries_raises_error(self) -> None:
        """Test undo raises error for empty manifest."""
        manifest = DeletionManifest(id="test123", mode="trash")

        manager = UndoManager()

        with pytest.raises(UndoUnavailableError):
            manager.undo(manifest)


class TestUndoManagerClearHistory:
    """Tests for UndoManager.clear_history."""

    def test_clear_history_with_manifests(self, fs: FakeFilesystem) -> None:
        """Test clear_history deletes manifests."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        for i in range(3):
            manifest = DeletionManifest(id=f"clear{i}", mode="trash")
            manifest.save(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        count = manager.clear_history()

        assert count == 3

    def test_clear_history_empty(self, fs: FakeFilesystem) -> None:
        """Test clear_history when empty."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        manager = UndoManager(storage_dir=storage_dir)
        count = manager.clear_history()

        assert count == 0

    def test_clear_history_storage_not_exists(self) -> None:
        """Test clear_history when storage doesn't exist."""
        manager = UndoManager(storage_dir=Path("/nonexistent"))
        count = manager.clear_history()

        assert count == 0


class TestUndoManagerExportHistory:
    """Tests for UndoManager.export_history."""

    def test_export_history_with_manifests(self, fs: FakeFilesystem) -> None:
        """Test export_history exports manifests."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        for i in range(2):
            manifest = DeletionManifest(id=f"export{i}", mode="trash", total_files=5)
            manifest.save(storage_dir)

        output_path = Path("/tmp/export.json")
        manager = UndoManager(storage_dir=storage_dir)
        count = manager.export_history(output_path)

        assert count == 2
        assert output_path.exists()

        with output_path.open() as f:
            data = json.load(f)
            assert "manifests" in data
            assert len(data["manifests"]) == 2

    def test_export_history_empty(self, fs: FakeFilesystem) -> None:
        """Test export_history when empty."""
        storage_dir = Path("/tmp/dmlclean_test")
        fs.create_dir(storage_dir)

        output_path = Path("/tmp/export.json")
        manager = UndoManager(storage_dir=storage_dir)
        count = manager.export_history(output_path)

        assert count == 0
        assert output_path.exists()
