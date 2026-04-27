"""
Integration tests for DMLClean pipeline.

Tests full Scanner → Analyzer → Filter → Executor flow.
"""

# ruff: noqa: S108  # reason: test file using pyfakefs - no real disk access

from __future__ import annotations

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from dmlclean.core.analyzer import Analyzer
from dmlclean.core.cleaner import Cleaner
from dmlclean.core.pipeline import Pipeline
from dmlclean.core.scanner import FileSystemScanner
from dmlclean.safety.protected_zone import ProtectedZone


class TestPipeline:
    """Integration tests for full pipeline."""

    @pytest.fixture
    def sample_filesystem(self, fake_fs: FakeFilesystem) -> list[Path]:
        """Create a sample filesystem tree for testing."""

        # Create various file types
        files = [
            # Temp files
            "/tmp/temp1.tmp",
            "/tmp/temp2.tmp",
            "/tmp/app.log",
            # Python artifacts
            "/project/__pycache__/module.pyc",
            "/project/.pytest_cache/README",
            # Browser-like cache
            "/browser/Cache/data_1",
            "/browser/Cache/data_2",
            # Protected files
            "/project/.git/config",
            "/project/venv/bin/python",
            # Normal files (should not be cleaned)
            "/documents/report.pdf",
            "/documents/notes.txt",
        ]

        for file_path in files:
            if ".git" in file_path or "venv" in file_path:
                # Protected files
                fake_fs.create_file(file_path, contents="protected content")
            else:
                fake_fs.create_file(file_path, contents="test content" * 10)

        return [Path(f) for f in files]

    async def test_full_pipeline_dry_run(
        self,
        sample_filesystem: list[Path],
        fake_fs: FakeFilesystem,
    ) -> None:
        """Test full pipeline in dry-run mode."""

        # Create pipeline with default settings
        pipeline = Pipeline(
            scanner=FileSystemScanner(),
            analyzer=Analyzer(category_configs={}),
            cleaner=Cleaner(mode="dry-run"),
            protected_zone=ProtectedZone(
                enabled=True,
                protect_git_dirs=True,
                protect_venvs=True,
            ),
        )

        # Run pipeline
        result = await pipeline.run(
            roots=[Path("/tmp"), Path("/project"), Path("/browser")],
            mode="dry-run",
        )

        # Verify scan worked
        assert result.scan_result is not None
        assert result.scan_result.stats.total_files > 0

        # Verify analysis worked
        assert result.analysis_result is not None

        # Verify manifest created
        assert result.manifest is not None

        # Verify no files were actually deleted (dry-run)
        for path in sample_filesystem:
            assert path.exists(), f"{path} should still exist after dry-run"

    async def test_protected_zone_enforcement(
        self,
        sample_filesystem: list[Path],
        fake_fs: FakeFilesystem,
    ) -> None:
        """Test that protected zone blocks protected paths."""

        pipeline = Pipeline(
            scanner=FileSystemScanner(),
            analyzer=Analyzer(category_configs={}),
            cleaner=Cleaner(
                mode="dry-run",
                protected_zone=ProtectedZone(
                    enabled=True,
                    protect_git_dirs=True,
                    protect_venvs=True,
                ),
            ),
        )

        result = await pipeline.run(
            roots=[Path("/project")],
            mode="dry-run",
        )

        # Protected files should be skipped
        if result.clean_result:
            protected_count = result.clean_result.stats.skipped
            assert protected_count > 0, "Protected files should be skipped"

    async def test_category_filtering(
        self,
        sample_filesystem: list[Path],
        fake_fs: FakeFilesystem,
    ) -> None:
        """Test filtering by category."""

        pipeline = Pipeline()

        # Filter by system_junk category (tmp files)
        result = await pipeline.run(
            roots=[Path("/tmp")],
            mode="dry-run",
            categories=["system_junk"],  # Only system junk
        )

        # Should only include system junk files from /tmp
        if result.analysis_result:
            for candidate in result.analysis_result.candidates:
                assert candidate.category.value == "system_junk"

    async def test_scan_only(self, sample_filesystem: list[Path]) -> None:
        """Test scan-only stage."""
        pipeline = Pipeline()

        result = await pipeline.scan_only([Path("/tmp")])

        assert result.stats.total_files > 0
        assert result.stats.errors == 0

    async def test_analyze_only(self, sample_filesystem: list[Path]) -> None:
        """Test analyze-only stage."""
        pipeline = Pipeline()

        result = await pipeline.analyze_only(sample_filesystem)

        assert len(result.candidates) > 0
        assert result.by_category != {}

    def test_sync_pipeline(self, sample_filesystem: list[Path]) -> None:
        """Test synchronous pipeline execution."""
        pipeline = Pipeline()

        result = pipeline.run_sync(
            roots=[Path("/tmp")],
            mode="dry-run",
        )

        assert result.scan_result is not None
        assert result.analysis_result is not None
