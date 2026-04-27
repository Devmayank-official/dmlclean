"""
Pipeline orchestration for DMLClean.

Coordinates the full cleaning pipeline:
Scanner → Analyzer → Filter → Reporter → Executor
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from dmlclean.core.analyzer import AnalysisResult, Analyzer, CleanCandidate
from dmlclean.core.cleaner import Cleaner, CleanResult
from dmlclean.core.scanner import FileSystemScanner, ScanResult
from dmlclean.safety.manifest import DeletionManifest
from dmlclean.safety.protected_zone import ProtectedZone


@dataclass
class PipelineResult:
    """
    Complete result of a pipeline execution.

    Attributes:
        scan_result: Result from the scanner.
        analysis_result: Result from the analyzer.
        clean_result: Result from the cleaner (if executed).
        manifest: Deletion manifest (preview or executed).
        errors: List of errors encountered.
    """

    scan_result: ScanResult | None = None
    analysis_result: AnalysisResult | None = None
    clean_result: CleanResult | None = None
    manifest: DeletionManifest | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scan": self.scan_result.stats.to_dict() if self.scan_result else None,
            "analysis": self.analysis_result.get_summary() if self.analysis_result else None,
            "clean": self.clean_result.to_dict() if self.clean_result else None,
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "errors": self.errors,
        }


class Pipeline:
    """
    Main pipeline orchestrator for DMLClean.

    Coordinates all stages of the cleaning process:
    1. Scan: Discover files in target paths
    2. Analyze: Categorize and assign risk levels
    3. Filter: Apply user filters (age, size, categories)
    4. Report: Generate preview/report
    5. Execute: Perform cleaning operation

    Attributes:
        scanner: File system scanner instance.
        analyzer: Analyzer instance.
        cleaner: Cleaner instance.
        protected_zone: Protected Zone instance.
    """

    def __init__(
        self,
        scanner: FileSystemScanner | None = None,
        analyzer: Analyzer | None = None,
        cleaner: Cleaner | None = None,
        protected_zone: ProtectedZone | None = None,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            scanner: File system scanner (created if None).
            analyzer: Analyzer (created if None).
            cleaner: Cleaner (created if None).
            protected_zone: Protected Zone (created if None).
        """
        self.scanner = scanner or FileSystemScanner()
        self.analyzer = analyzer or Analyzer()
        self.protected_zone = protected_zone or ProtectedZone(enabled=True)
        self.cleaner = cleaner or Cleaner(
            mode="dry-run",
            protected_zone=self.protected_zone,
        )

        logger.info("Pipeline initialized")

    async def run(
        self,
        roots: list[Path],
        mode: str = "dry-run",
        categories: list[str] | None = None,
        min_age_days: int = 0,
        min_size_mb: int = 0,
        progress_callback: Callable[[str, int, Any], None] | None = None,
    ) -> PipelineResult:
        """
        Run the full cleaning pipeline.

        Args:
            roots: Root paths to scan.
            mode: Clean mode ('dry-run', 'trash', 'permanent').
            categories: Categories to include (None = all enabled).
            min_age_days: Minimum file age in days.
            min_size_mb: Minimum file size in MB.
            progress_callback: Optional callback(stage, count, data).

        Returns:
            PipelineResult: Complete pipeline result.
        """
        result = PipelineResult()
        errors: list[str] = []

        try:
            # Stage 1: Scan
            if progress_callback:
                progress_callback("scan", 0, {"roots": [str(r) for r in roots]})

            logger.info(f"Starting scan of {len(roots)} roots")
            scan_result = await self.scanner.scan(roots)
            result.scan_result = scan_result

            if progress_callback:
                progress_callback(
                    "scan", scan_result.stats.total_files, scan_result.stats.to_dict()
                )

            logger.info(f"Scan complete: {scan_result.stats.total_files} files found")

            # Stage 2: Analyze
            if progress_callback:
                progress_callback("analyze", 0, {})

            logger.info("Starting analysis")
            analysis_result = self.analyzer.analyze(scan_result.paths)
            result.analysis_result = analysis_result

            if progress_callback:
                progress_callback(
                    "analyze", len(analysis_result.candidates), analysis_result.get_summary()
                )

            logger.info(f"Analysis complete: {len(analysis_result.candidates)} candidates")

            # Stage 3: Filter by categories
            if categories:
                filtered_candidates = [
                    c for c in analysis_result.candidates if c.category.value in categories
                ]
                logger.info(
                    f"Filtered to {len(filtered_candidates)} candidates (categories: {categories})"
                )
            else:
                filtered_candidates = analysis_result.candidates

            # Stage 4: Create manifest (preview)
            if mode == "dry-run":
                manifest = self.cleaner.preview(filtered_candidates)
                result.manifest = manifest
                logger.info(
                    f"Preview manifest created: {manifest.total_files} files, "
                    f"{manifest.total_size_bytes} bytes"
                )

            # Stage 5: Execute (if not dry-run)
            if mode != "dry-run":
                if progress_callback:
                    progress_callback("clean", 0, {"mode": mode})

                # Update cleaner mode
                self.cleaner.mode = mode

                logger.info(f"Starting {mode} operation")
                clean_result = await self.cleaner.clean(
                    filtered_candidates,
                    progress_callback=lambda count, candidate: None,  # Could wire through
                )
                result.clean_result = clean_result
                result.manifest = clean_result.manifest

                if progress_callback:
                    progress_callback(
                        "clean", clean_result.stats.deleted, clean_result.stats.to_dict()
                    )

                logger.info(
                    f"Clean operation complete: {clean_result.stats.deleted} deleted, "
                    f"{clean_result.stats.failed} failed"
                )

        except Exception as e:
            error_msg = f"Pipeline error: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
            result.errors = errors

        return result

    def run_sync(
        self,
        roots: list[Path],
        mode: str = "dry-run",
        categories: list[str] | None = None,
        min_age_days: int = 0,
        min_size_mb: int = 0,
        progress_callback: Callable[[str, int, Any], None] | None = None,
    ) -> PipelineResult:
        """
        Synchronous wrapper for pipeline execution.

        Args:
            roots: Root paths to scan.
            mode: Clean mode.
            categories: Categories to include.
            min_age_days: Minimum file age.
            min_size_mb: Minimum file size.
            progress_callback: Progress callback.

        Returns:
            PipelineResult: Complete result.
        """
        return asyncio.run(
            self.run(
                roots,
                mode,
                categories,
                min_age_days,
                min_size_mb,
                progress_callback,
            )
        )

    async def scan_only(
        self,
        roots: list[Path],
    ) -> ScanResult:
        """
        Run only the scan stage.

        Args:
            roots: Root paths to scan.

        Returns:
            ScanResult: Scan result.
        """
        return await self.scanner.scan(roots)

    async def analyze_only(
        self,
        paths: list[Path],
    ) -> AnalysisResult:
        """
        Run only the analysis stage.

        Args:
            paths: Paths to analyze.

        Returns:
            AnalysisResult: Analysis result.
        """
        return self.analyzer.analyze(paths)

    def get_preview(
        self,
        candidates: list[CleanCandidate],
    ) -> DeletionManifest:
        """
        Get a preview manifest without executing.

        Args:
            candidates: Candidates to preview.

        Returns:
            DeletionManifest: Preview manifest.
        """
        return self.cleaner.preview(candidates)

    def check_protected(
        self,
        paths: list[Path],
    ) -> dict[Path, tuple[bool, str]]:
        """
        Check if paths are protected.

        Args:
            paths: Paths to check.

        Returns:
            dict[Path, tuple[bool, str]]: Mapping of path to (is_protected, reason).
        """
        result = {}
        for path in paths:
            protection = self.protected_zone.is_protected(path)
            result[path] = (protection.is_protected, protection.reason)
        return result
