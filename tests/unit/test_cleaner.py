"""
Unit tests for DMLClean cleaner module.

Tests dry-run, trash, and permanent deletion modes.
"""

# ruff: noqa: S108  # reason: test file using pyfakefs - no real disk access

from __future__ import annotations

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.core.analyzer import CleanCandidate, RiskLevel
from dmlclean.core.cleaner import Cleaner, CleanResult
from dmlclean.safety.protected_zone import ProtectedZone


class TestCleaner:
    """Tests for Cleaner."""

    @pytest.fixture
    def cleaner_dry_run(self) -> Cleaner:
        """Create a dry-run cleaner."""
        return Cleaner(
            mode="dry-run",
            protected_zone=ProtectedZone(enabled=False, protect_recent_days=0),
        )

    @pytest.fixture
    def cleaner_trash(self) -> Cleaner:
        """Create a trash mode cleaner."""
        return Cleaner(
            mode="trash",
            protected_zone=ProtectedZone(enabled=False, protect_recent_days=0),
        )

    @pytest.fixture
    def sample_candidates(self, fake_fs: FakeFilesystem) -> list[CleanCandidate]:
        """Create sample candidates for testing."""
        from pathlib import Path

        files = [
            "/tmp/test1.tmp",
            "/tmp/test2.log",
            "/cache/file.dat",
        ]
        for file_path in files:
            fake_fs.create_file(file_path, contents="test content" * 100)

        return [
            CleanCandidate(
                path=Path(f),
                category="test",
                size_bytes=1000,
                risk_level=RiskLevel.LOW,
                reason="Test file",
                last_modified=None,  # Don't set mtime to avoid recent file protection
            )
            for f in files
        ]

    async def test_dry_run_no_changes(
        self,
        cleaner_dry_run: Cleaner,
        sample_candidates: list[CleanCandidate],
        fake_fs: FakeFilesystem,
    ) -> None:
        """Test that dry-run mode makes no changes."""
        from pathlib import Path

        # Verify files exist before
        for candidate in sample_candidates:
            assert Path(candidate.path).exists()

        result = await cleaner_dry_run.clean(sample_candidates)

        # All files should still exist after dry-run
        for candidate in sample_candidates:
            assert Path(candidate.path).exists()

        # Manifest should be created
        assert result.manifest.total_files == len(sample_candidates)

    async def test_clean_with_protected_zone(
        self,
        cleaner_dry_run: Cleaner,
        fake_fs: FakeFilesystem,
    ) -> None:
        """Test that protected paths are skipped."""
        from pathlib import Path

        # Create protected and non-protected files
        fake_fs.create_file("/tmp/safe.tmp", contents="safe")
        fake_fs.create_file("/project/.git/config", contents="protected")

        protected_zone = ProtectedZone(
            enabled=True,
            protected_paths=["**/.git/**"],
        )
        cleaner = Cleaner(mode="dry-run", protected_zone=protected_zone)

        candidates = [
            CleanCandidate(
                path=Path("/tmp/safe.tmp"),
                category="test",
                size_bytes=10,
                risk_level=RiskLevel.LOW,
                reason="Safe file",
            ),
            CleanCandidate(
                path=Path("/project/.git/config"),
                category="test",
                size_bytes=10,
                risk_level=RiskLevel.HIGH,
                reason="Protected file",
            ),
        ]

        result = await cleaner.clean(candidates)

        # Protected file should be skipped
        assert result.stats.skipped >= 1

    def test_clean_sync_wrapper(
        self,
        cleaner_dry_run: Cleaner,
        sample_candidates: list[CleanCandidate],
    ) -> None:
        """Test synchronous wrapper method."""
        result = cleaner_dry_run.clean_sync(sample_candidates)

        assert isinstance(result, CleanResult)
        assert result.manifest is not None

    async def test_preview_mode(
        self,
        cleaner_dry_run: Cleaner,
        sample_candidates: list[CleanCandidate],
    ) -> None:
        """Test preview manifest creation."""
        manifest = cleaner_dry_run.preview(sample_candidates)

        assert manifest.total_files == len(sample_candidates)
        assert manifest.mode == "dry-run"
