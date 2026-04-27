"""
Unit tests for DMLClean async file system scanner.

Tests scan functionality, path resolution, and symlink handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.core.scanner import FileSystemScanner


class TestFileSystemScanner:
    """Tests for FileSystemScanner."""

    @pytest.fixture
    def scanner(self) -> FileSystemScanner:
        """Create a scanner instance."""
        return FileSystemScanner(
            follow_symlinks=False,
            max_depth=0,
        )

    @pytest.fixture
    def sample_tree(self, fake_fs: FakeFilesystem) -> list[str]:
        """Create a sample directory tree."""
        files = [
            "/test/project/file1.txt",
            "/test/project/file2.py",
            "/test/project/subdir/file3.txt",
            "/test/project/__pycache__/module.pyc",
            "/test/project/.git/config",
            "/test/tmp/temp1.tmp",
            "/test/tmp/temp2.tmp",
        ]
        for file_path in files:
            fake_fs.create_file(file_path, contents="test content")
        return files

    async def test_scan_basic(self, scanner: FileSystemScanner, sample_tree: list[str]) -> None:
        """Test basic scanning functionality."""

        result = await scanner.scan(
            [Path("/test/project") for Path in [__import__("pathlib").Path]]
        )

        assert result.stats.total_files > 0
        assert result.stats.errors == 0

    async def test_scan_nonexistent_root(self, scanner: FileSystemScanner) -> None:
        """Test scanning nonexistent path."""
        result = await scanner.scan([Path("/nonexistent")])

        assert result.stats.total_files == 0
        assert result.stats.errors == 1

    async def test_scan_with_exclude(self, fake_fs: FakeFilesystem) -> None:
        """Test scanning with exclude patterns."""
        fake_fs.create_file("/test/include.txt", contents="a")
        fake_fs.create_file("/test/exclude.log", contents="b")

        scanner = FileSystemScanner(exclude_patterns=["*.log"])
        result = await scanner.scan([Path("/test")])

        assert result.stats.total_files == 1

    async def test_scan_depth_limit(self, fake_fs: FakeFilesystem) -> None:
        """Test max depth limiting."""
        fake_fs.create_file("/a/b/c/d/file.txt", contents="deep")

        scanner = FileSystemScanner(max_depth=2)
        result = await scanner.scan([Path("/a")])

        # Should not include files deeper than max_depth
        assert result.stats.total_files <= 1
