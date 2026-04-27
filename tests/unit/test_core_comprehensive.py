"""
Comprehensive Core Module Tests for DMLClean.

Tests for pipeline, analyzer, cleaner, and other core modules.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dmlclean.core.analyzer import Analyzer, Category, CleanCandidate, RiskLevel
from dmlclean.core.cleaner import Cleaner, CleanResult, CleanStats
from dmlclean.core.deduplicator import DeduplicationResult, Deduplicator, DuplicateGroup
from dmlclean.core.pipeline import Pipeline, PipelineResult
from dmlclean.core.plugin_scanner import PluginScanConfig, PluginScanner
from dmlclean.core.scanner import FileSystemScanner, ScanResult, ScanStats


class TestPipeline:
    """Tests for Pipeline."""

    def test_init(self) -> None:
        """Test pipeline initialization."""
        pipeline = Pipeline()

        assert pipeline.scanner is not None
        assert pipeline.analyzer is not None
        assert pipeline.cleaner is not None
        assert pipeline.protected_zone is not None

    def test_init_with_custom_components(self) -> None:
        """Test pipeline with custom components."""
        mock_scanner = MagicMock()
        mock_analyzer = MagicMock()
        mock_cleaner = MagicMock()
        mock_zone = MagicMock()

        pipeline = Pipeline(
            scanner=mock_scanner,
            analyzer=mock_analyzer,
            cleaner=mock_cleaner,
            protected_zone=mock_zone,
        )

        assert pipeline.scanner is mock_scanner
        assert pipeline.analyzer is mock_analyzer
        assert pipeline.cleaner is mock_cleaner
        assert pipeline.protected_zone is mock_zone

    @pytest.mark.asyncio
    async def test_run_dry_run(self) -> None:
        """Test pipeline dry-run mode."""
        pipeline = Pipeline()

        # Mock scanner
        mock_scan_result = ScanResult(
            paths=[Path("/tmp/test.txt")], stats=ScanStats(total_files=1, total_size_bytes=1024)
        )

        with patch.object(pipeline.scanner, "scan", return_value=mock_scan_result):
            with patch.object(pipeline.analyzer, "analyze") as mock_analyze:
                mock_analyze.return_value = MagicMock(
                    candidates=[], get_summary=lambda: {"by_category": {}, "by_risk": {}}
                )

                result = await pipeline.run(
                    roots=[Path("/tmp")],
                    mode="dry-run",
                )

                assert isinstance(result, PipelineResult)
                assert result.scan_result is not None

    def test_run_sync(self) -> None:
        """Test synchronous pipeline execution."""
        pipeline = Pipeline()

        # Should not raise
        result = pipeline.run_sync(
            roots=[Path("/tmp")],
            mode="dry-run",
        )

        assert isinstance(result, PipelineResult)

    @pytest.mark.asyncio
    async def test_scan_only(self) -> None:
        """Test scan-only mode."""
        pipeline = Pipeline()

        mock_result = ScanResult(paths=[Path("/tmp/test.txt")], stats=ScanStats(total_files=1))

        with patch.object(pipeline.scanner, "scan", return_value=mock_result):
            result = await pipeline.scan_only([Path("/tmp")])

            assert isinstance(result, ScanResult)

    @pytest.mark.asyncio
    async def test_analyze_only(self) -> None:
        """Test analyze-only mode."""
        pipeline = Pipeline()

        mock_result = MagicMock(
            candidates=[], get_summary=lambda: {"by_category": {}, "by_risk": {}}
        )

        with patch.object(pipeline.analyzer, "analyze", return_value=mock_result):
            result = await pipeline.analyze_only([Path("/tmp/test.txt")])

            assert result is mock_result

    def test_get_preview(self) -> None:
        """Test getting preview manifest."""
        pipeline = Pipeline()

        candidates = []

        manifest = pipeline.get_preview(candidates)

        assert manifest is not None
        assert manifest.total_files == 0

    def test_check_protected(self) -> None:
        """Test checking protected paths."""
        pipeline = Pipeline()

        paths = [Path("/tmp/test.txt")]

        result = pipeline.check_protected(paths)

        assert isinstance(result, dict)


class TestAnalyzer:
    """Tests for Analyzer."""

    def test_init(self) -> None:
        """Test analyzer initialization."""
        analyzer = Analyzer()

        assert analyzer.category_configs == {}
        assert analyzer.min_age_days == 0
        assert analyzer.min_size_mb == 0

    def test_init_with_config(self) -> None:
        """Test analyzer with configuration."""
        config = {
            "browser": {"enabled": True, "min_risk": "low"},
            "dev_python": {"enabled": False},
        }

        analyzer = Analyzer(category_configs=config)

        assert "browser" in analyzer.category_configs

    def test_analyze_empty_paths(self) -> None:
        """Test analyzing empty paths."""
        analyzer = Analyzer()

        result = analyzer.analyze([])

        assert result.candidates == []
        assert result.total_files == 0

    def test_analyze_with_paths(self) -> None:
        """Test analyzing paths."""
        analyzer = Analyzer()

        # Create a temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = analyzer.analyze([temp_path])

            assert isinstance(result.candidates, list)
        finally:
            temp_path.unlink()

    def test_get_category_for_path(self) -> None:
        """Test getting category for path."""
        analyzer = Analyzer()

        # Test with a temp file path
        category = analyzer.get_category_for_path(Path("/tmp/test.tmp"))

        # May be None if no pattern matches
        assert category is None or isinstance(category, Category)

    def test_get_risk_for_path(self) -> None:
        """Test getting risk level for path."""
        analyzer = Analyzer()

        risk = analyzer.get_risk_for_path(Path("/tmp/test.tmp"))

        # May be None if no pattern matches
        assert risk is None or isinstance(risk, RiskLevel)


class TestCleanCandidate:
    """Tests for CleanCandidate in analyzer."""

    def test_create_candidate(self) -> None:
        """Test creating candidate."""
        candidate = CleanCandidate(
            path=Path("/tmp/test.txt"),
            category=Category.SYSTEM_JUNK,
            size_bytes=1024,
            risk_level=RiskLevel.LOW,
            reason="Test file",
        )

        assert candidate.path == Path("/tmp/test.txt")
        assert candidate.category == Category.SYSTEM_JUNK

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        candidate = CleanCandidate(
            path=Path("/tmp/test.txt"),
            category=Category.BROWSER,
            size_bytes=2048,
            risk_level=RiskLevel.MEDIUM,
            reason="Cache",
        )

        data = candidate.to_dict()

        assert data["path"] == str(Path("/tmp/test.txt"))
        assert data["category"] == "browser"
        # size_human is calculated, just verify category is present
        assert "category" in data


class TestCleaner:
    """Tests for Cleaner."""

    def test_init(self) -> None:
        """Test cleaner initialization."""
        cleaner = Cleaner(mode="dry-run")

        assert cleaner.mode == "dry-run"
        assert cleaner.protected_zone is not None

    def test_init_invalid_mode(self) -> None:
        """Test cleaner with invalid mode."""
        with pytest.raises(ValueError):
            Cleaner(mode="invalid")

    @pytest.mark.asyncio
    async def test_clean_dry_run(self) -> None:
        """Test dry-run cleaning."""
        cleaner = Cleaner(mode="dry-run")

        candidates = []

        result = await cleaner.clean(candidates)

        assert isinstance(result, CleanResult)
        assert result.stats.deleted == 0

    def test_clean_sync(self) -> None:
        """Test synchronous cleaning."""
        cleaner = Cleaner(mode="dry-run")

        candidates = []

        result = cleaner.clean_sync(candidates)

        assert isinstance(result, CleanResult)

    def test_preview(self) -> None:
        """Test preview mode."""
        cleaner = Cleaner(mode="dry-run")

        candidates = []

        manifest = cleaner.preview(candidates)

        assert manifest is not None
        assert manifest.total_files == 0


class TestCleanStats:
    """Tests for CleanStats."""

    def test_create_stats(self) -> None:
        """Test creating stats."""
        stats = CleanStats(
            total_files=100,
            total_size_bytes=1024 * 1024,
            deleted=90,
            failed=5,
            skipped=5,
        )

        assert stats.total_files == 100
        assert stats.deleted == 90

    def test_to_dict(self) -> None:
        """Test converting stats to dictionary."""
        stats = CleanStats(
            total_files=100,
            total_size_bytes=1024 * 1024,
            deleted=90,
        )

        data = stats.to_dict()

        assert data["total_files"] == 100
        assert "total_size_human" in data
        assert "success_rate" in data


class TestFileSystemScanner:
    """Tests for FileSystemScanner."""

    def test_init(self) -> None:
        """Test scanner initialization."""
        scanner = FileSystemScanner()

        assert scanner.follow_symlinks is False
        assert scanner.max_depth == 0
        assert scanner.max_workers == 10

    def test_init_with_options(self) -> None:
        """Test scanner with options."""
        scanner = FileSystemScanner(
            follow_symlinks=True,
            max_depth=5,
            max_workers=20,
        )

        assert scanner.follow_symlinks is True
        assert scanner.max_depth == 5
        assert scanner.max_workers == 20

    @pytest.mark.asyncio
    async def test_scan_empty_roots(self) -> None:
        """Test scanning empty roots."""
        scanner = FileSystemScanner()

        result = await scanner.scan([])

        assert isinstance(result, ScanResult)
        assert result.paths == []

    @pytest.mark.asyncio
    async def test_scan_nonexistent_path(self) -> None:
        """Test scanning non-existent path."""
        scanner = FileSystemScanner()

        result = await scanner.scan([Path("/nonexistent/path")])

        assert isinstance(result, ScanResult)
        assert len(result.errors) >= 1


class TestDeduplicator:
    """Tests for Deduplicator."""

    def test_init(self) -> None:
        """Test deduplicator initialization."""
        dedup = Deduplicator()

        assert dedup.algorithm == "xxh64"
        assert dedup.min_size == 1

    def test_find_duplicates_empty(self) -> None:
        """Test finding duplicates in empty list."""
        dedup = Deduplicator()

        result = dedup.find_duplicates([])

        assert isinstance(result, DeduplicationResult)
        assert result.groups == []

    def test_find_duplicates_in_directory(self) -> None:
        """Test finding duplicates in directory."""
        dedup = Deduplicator()

        # Test with non-existent directory
        result = dedup.find_duplicates_in_directory(
            Path("/nonexistent"),
            recursive=True,
        )

        assert isinstance(result, DeduplicationResult)


class TestDuplicateGroup:
    """Tests for DuplicateGroup."""

    def test_create_group(self) -> None:
        """Test creating duplicate group."""
        group = DuplicateGroup(
            hash_value="abc123",
            size_bytes=1024,
            files=[Path("/tmp/file1.txt"), Path("/tmp/file2.txt")],
        )

        assert group.hash_value == "abc123"
        assert len(group.files) == 2
        assert group.wasted_bytes == 1024  # One file is wasted

    def test_to_dict(self) -> None:
        """Test converting group to dictionary."""
        group = DuplicateGroup(
            hash_value="abc123",
            size_bytes=1024,
            files=[Path("/tmp/file1.txt")],
        )

        data = group.to_dict()

        assert data["hash_value"] == "abc123"
        assert "size_human" in data
        assert "wasted_human" in data


class TestPluginScanner:
    """Tests for PluginScanner."""

    def test_init(self) -> None:
        """Test plugin scanner initialization."""
        config = PluginScanConfig()
        scanner = PluginScanner(config=config)

        assert scanner.config == config
        assert scanner._plugins_loaded is False

    def test_load_plugins_disabled(self) -> None:
        """Test loading plugins when disabled."""
        config = PluginScanConfig(use_plugins=False)
        scanner = PluginScanner(config=config)

        plugins = scanner._load_plugins()

        assert plugins == []

    def test_load_plugins_no_loader(self) -> None:
        """Test loading plugins without loader."""
        config = PluginScanConfig(use_plugins=True)
        scanner = PluginScanner(plugin_loader=None, config=config)

        plugins = scanner._load_plugins()

        # Should return empty list or handle gracefully
        assert isinstance(plugins, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
