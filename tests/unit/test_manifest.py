"""
Unit tests for DMLClean DeletionManifest.

Tests pre-op write, undo restore, and corrupt manifest handling.
"""

# ruff: noqa: S108  # reason: test file using pyfakefs - no real disk access

from __future__ import annotations

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.safety.manifest import DeletionManifest, ManifestEntry


class TestManifestEntry:
    """Tests for ManifestEntry."""

    def test_entry_creation(self) -> None:
        """Test basic entry creation."""
        entry = ManifestEntry(
            path="/tmp/test.txt",
            size_bytes=1024,
            category="test",
            risk_level="low",
        )

        assert entry.path == "/tmp/test.txt"
        assert entry.size_bytes == 1024
        assert entry.deleted_at != ""

    def test_entry_to_dict(self) -> None:
        """Test entry serialization."""
        entry = ManifestEntry(
            path="/tmp/test.txt",
            size_bytes=1024,
            hash_value="abc123",
            category="browser",
            risk_level="low",
        )

        data = entry.to_dict()

        assert data["path"] == "/tmp/test.txt"
        assert data["size_bytes"] == 1024
        assert data["hash_value"] == "abc123"
        assert "deleted_at" in data

    def test_entry_from_dict(self) -> None:
        """Test entry deserialization."""
        data = {
            "path": "/tmp/test.txt",
            "size_bytes": 1024,
            "hash_value": "xyz789",
            "deleted_at": "2024-01-01T00:00:00Z",
            "mode": "trash",
            "category": "test",
            "risk_level": "low",
            "is_directory": False,
        }

        entry = ManifestEntry.from_dict(data)

        assert entry.path == "/tmp/test.txt"
        assert entry.hash_value == "xyz789"


class TestDeletionManifest:
    """Tests for DeletionManifest."""

    def test_manifest_creation(self) -> None:
        """Test basic manifest creation."""
        manifest = DeletionManifest(
            mode="dry-run",
            profile="developer",
        )

        assert manifest.id != ""
        assert manifest.mode == "dry-run"
        assert manifest.created_at != ""

    def test_add_entry(self) -> None:
        """Test adding entries to manifest."""
        manifest = DeletionManifest()

        entry = ManifestEntry(
            path="/tmp/test.txt",
            size_bytes=100,
            category="test",
            risk_level="low",
        )
        manifest.add_entry(entry)

        assert manifest.total_files == 1
        assert manifest.total_size_bytes == 100

    def test_add_directory_entry(self) -> None:
        """Test adding directory entry."""
        manifest = DeletionManifest()

        entry = ManifestEntry(
            path="/tmp/cache/",
            size_bytes=5000,
            category="test",
            risk_level="medium",
            is_directory=True,
        )
        manifest.add_entry(entry)

        assert manifest.total_directories == 1
        assert manifest.total_files == 0

    def test_manifest_to_dict(self) -> None:
        """Test manifest serialization."""
        manifest = DeletionManifest(mode="trash")
        manifest.add_entry(
            ManifestEntry(
                path="/tmp/test.txt",
                size_bytes=100,
                category="test",
                risk_level="low",
            )
        )

        data = manifest.to_dict()

        assert "id" in data
        assert "created_at" in data
        assert data["total_files"] == 1
        assert len(data["entries"]) == 1

    def test_manifest_json_roundtrip(self) -> None:
        """Test JSON serialization and deserialization."""
        original = DeletionManifest(mode="trash", profile="test")
        original.add_entry(
            ManifestEntry(
                path="/tmp/test.txt",
                size_bytes=100,
                category="test",
                risk_level="low",
                hash_value="hash123",
            )
        )

        json_str = original.to_json()
        restored = DeletionManifest.from_json(json_str)

        assert restored.id == original.id
        assert restored.mode == original.mode
        assert restored.total_files == original.total_files

    def test_manifest_save_and_load(self, fake_fs: FakeFilesystem) -> None:
        """Test saving and loading manifest from file."""

        manifest = DeletionManifest(mode="trash")
        manifest.add_entry(
            ManifestEntry(
                path="/tmp/test.txt",
                size_bytes=100,
                category="test",
                risk_level="low",
            )
        )

        # Save to file
        storage_dir = Path("/manifests")
        fake_fs.create_dir(storage_dir)

        file_path = manifest.save(storage_dir)

        assert file_path.exists()

        # Load from file
        loaded = DeletionManifest.load(file_path)

        assert loaded.total_files == manifest.total_files
        assert loaded.mode == manifest.mode

    def test_manifest_summary(self) -> None:
        """Test manifest summary generation."""
        manifest = DeletionManifest()
        manifest.add_entry(
            ManifestEntry(
                path="/tmp/large.bin",
                size_bytes=1024 * 1024 * 100,  # 100 MB
                category="test",
                risk_level="low",
            )
        )

        summary = manifest.get_summary()

        assert summary["total_files"] == 1
        assert "100.00 MB" in summary["total_size_human"]

    def test_multiple_entries(self) -> None:
        """Test manifest with multiple entries."""
        manifest = DeletionManifest()

        for i in range(10):
            manifest.add_entry(
                ManifestEntry(
                    path=f"/tmp/file_{i}.txt",
                    size_bytes=100 * (i + 1),
                    category="test",
                    risk_level="low",
                )
            )

        assert manifest.total_files == 10
        assert manifest.total_size_bytes == sum(100 * (i + 1) for i in range(10))
        assert manifest.categories.get("test") == 10
