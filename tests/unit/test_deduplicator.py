"""
Unit tests for DMLClean deduplicator.

Tests xxhash-based duplicate file grouping.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.core.deduplicator import Deduplicator


class TestDeduplicator:
    """Tests for Deduplicator."""

    @pytest.fixture
    def deduplicator(self) -> Deduplicator:
        """Create a deduplicator instance."""
        return Deduplicator(algorithm="xxh64", min_size=1)

    @pytest.fixture
    def duplicate_files(self, fake_fs: FakeFilesystem) -> list[Path]:
        """Create files with duplicates."""

        # Create files with same content (duplicates)
        content = "This is duplicate content" * 100
        fake_fs.create_file("/files/original.txt", contents=content)
        fake_fs.create_file("/files/copy1.txt", contents=content)
        fake_fs.create_file("/files/copy2.txt", contents=content)

        # Create unique file
        fake_fs.create_file("/files/unique.txt", contents="unique content")

        return [
            Path("/files/original.txt"),
            Path("/files/copy1.txt"),
            Path("/files/copy2.txt"),
            Path("/files/unique.txt"),
        ]

    def test_find_duplicates(
        self,
        deduplicator: Deduplicator,
        duplicate_files: list[Path],
    ) -> None:
        """Test finding duplicate files."""
        result = deduplicator.find_duplicates(duplicate_files)

        # Should find one group of 3 duplicates
        assert len(result.groups) == 1
        assert result.total_duplicates == 2  # 2 extra copies
        assert result.files_scanned == 4

    def test_no_duplicates(self, fake_fs: FakeFilesystem) -> None:
        """Test with no duplicates."""

        fake_fs.create_file("/files/a.txt", contents="content a")
        fake_fs.create_file("/files/b.txt", contents="content b")
        fake_fs.create_file("/files/c.txt", contents="content c")

        deduplicator = Deduplicator()
        paths = [
            Path("/files/a.txt"),
            Path("/files/b.txt"),
            Path("/files/c.txt"),
        ]

        result = deduplicator.find_duplicates(paths)

        assert len(result.groups) == 0
        assert result.total_duplicates == 0

    def test_min_size_filter(self, fake_fs: FakeFilesystem) -> None:
        """Test minimum size filter."""

        # Small files (should be filtered)
        fake_fs.create_file("/files/small1.txt", contents="a")
        fake_fs.create_file("/files/small2.txt", contents="a")

        deduplicator = Deduplicator(min_size=100)
        paths = [
            Path("/files/small1.txt"),
            Path("/files/small2.txt"),
        ]

        result = deduplicator.find_duplicates(paths)

        # Files too small, no duplicates found
        assert result.total_duplicates == 0

    def test_duplicate_group_properties(
        self,
        deduplicator: Deduplicator,
        duplicate_files: list[Path],
    ) -> None:
        """Test duplicate group properties."""
        result = deduplicator.find_duplicates(duplicate_files)

        if result.groups:
            group = result.groups[0]

            assert group.size_bytes > 0
            assert len(group.files) == 3
            assert group.wasted_bytes == group.size_bytes * 2

    def test_duplicate_to_dict(
        self,
        deduplicator: Deduplicator,
        duplicate_files: list[Path],
    ) -> None:
        """Test duplicate group serialization."""
        result = deduplicator.find_duplicates(duplicate_files)

        if result.groups:
            group_dict = result.groups[0].to_dict()

            assert "hash_value" in group_dict
            assert "size_bytes" in group_dict
            assert "size_human" in group_dict
            assert "files" in group_dict
            assert "count" in group_dict
            assert "wasted_bytes" in group_dict

    def test_result_to_dict(
        self,
        deduplicator: Deduplicator,
        duplicate_files: list[Path],
    ) -> None:
        """Test deduplication result serialization."""
        result = deduplicator.find_duplicates(duplicate_files)
        result_dict = result.to_dict()

        assert "groups" in result_dict
        assert "total_duplicates" in result_dict
        assert "total_wasted_bytes" in result_dict
        assert "files_scanned" in result_dict

    def test_empty_file_list(self, deduplicator: Deduplicator) -> None:
        """Test with empty file list."""
        result = deduplicator.find_duplicates([])

        assert len(result.groups) == 0
        assert result.total_duplicates == 0
        assert result.files_scanned == 0
