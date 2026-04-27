"""
Cleaner execution pipeline for DMLClean.

Handles the actual deletion operations (dry-run, trash, permanent)
with proper safety checks, manifest logging, and error handling.
"""

from __future__ import annotations

import asyncio
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger
from send2trash import send2trash

from dmlclean.core.analyzer import CleanCandidate
from dmlclean.safety.manifest import DeletionManifest, ManifestEntry
from dmlclean.safety.protected_zone import ProtectedZone


@dataclass
class CleanStats:
    """
    Statistics from a cleaning operation.

    Attributes:
        total_files: Total number of files processed.
        total_directories: Total number of directories processed.
        total_size_bytes: Total size processed.
        deleted: Number of items successfully deleted.
        failed: Number of items that failed to delete.
        skipped: Number of items skipped (protected, etc.).
        duration_seconds: Time taken for the operation.
    """

    total_files: int = 0
    total_directories: int = 0
    total_size_bytes: int = 0
    deleted: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size_bytes": self.total_size_bytes,
            "total_size_human": self._humanize_size(self.total_size_bytes),
            "deleted": self.deleted,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": round(self.duration_seconds, 2),
            "success_rate": (
                f"{(self.deleted / (self.deleted + self.failed) * 100):.1f}%"
                if (self.deleted + self.failed) > 0
                else "0.0%"
            ),
        }

    @staticmethod
    def _humanize_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        size: float = size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"


@dataclass
class CleanResult:
    """
    Result of a cleaning operation.

    Attributes:
        manifest: Deletion manifest for this operation.
        stats: Cleaning statistics.
        deleted_paths: List of successfully deleted paths.
        failed_paths: List of paths that failed to delete.
        skipped_paths: List of skipped paths with reasons.
        errors: List of errors encountered.
    """

    manifest: DeletionManifest
    stats: CleanStats = field(default_factory=CleanStats)
    deleted_paths: list[Path] = field(default_factory=list)
    failed_paths: list[tuple[Path, str]] = field(default_factory=list)
    skipped_paths: list[tuple[Path, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "manifest_id": self.manifest.id,
            "mode": self.manifest.mode,
            "stats": self.stats.to_dict(),
            "deleted": [str(p) for p in self.deleted_paths],
            "failed": [{"path": str(p), "error": e} for p, e in self.failed_paths],
            "skipped": [{"path": str(p), "reason": r} for p, r in self.skipped_paths],
            "errors": self.errors,
        }


class Cleaner:
    """
    Cleaner execution engine for DMLClean.

    Handles deletion operations with:
    - Multiple modes (dry-run, trash, permanent)
    - Protected Zone enforcement
    - Manifest logging
    - Progress tracking
    - Error resilience

    Attributes:
        mode: Clean mode (dry-run, trash, permanent).
        protected_zone: Protected Zone instance.
        max_workers: Maximum concurrent operations.
    """

    def __init__(
        self,
        mode: str = "dry-run",
        protected_zone: ProtectedZone | None = None,
        max_workers: int = 5,
    ) -> None:
        """
        Initialize the cleaner.

        Args:
            mode: Clean mode ('dry-run', 'trash', 'permanent').
            protected_zone: Protected Zone for safety checks.
            max_workers: Maximum concurrent delete operations.
        """
        if mode not in ("dry-run", "trash", "permanent"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'dry-run', 'trash', or 'permanent'")

        self.mode = mode
        self.protected_zone = protected_zone or ProtectedZone(enabled=True)
        self.max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)

        logger.info(f"Cleaner initialized: mode={mode}, max_workers={max_workers}")

    async def clean(
        self,
        candidates: list[CleanCandidate],
        progress_callback: Callable[[int, CleanCandidate], None] | None = None,
    ) -> CleanResult:
        """
        Execute cleaning operation on candidates.

        Args:
            candidates: List of candidates to clean.
            progress_callback: Optional callback(count, candidate).

        Returns:
            CleanResult: Complete result with stats and manifest.
        """
        start_time = time.time()

        # Create manifest
        manifest = DeletionManifest(
            mode=self.mode,
            operation_id=f"clean_{int(start_time)}",
        )

        # Initialize result
        result = CleanResult(manifest=manifest)
        stats = CleanStats(
            total_files=len([c for c in candidates if not c.is_directory]),
            total_directories=len([c for c in candidates if c.is_directory]),
            total_size_bytes=sum(c.size_bytes for c in candidates),
        )

        logger.info(f"Starting {self.mode} operation on {len(candidates)} candidates")

        # Process candidates
        for candidate in candidates:
            try:
                # Check Protected Zone
                if self.protected_zone.enabled:
                    protection = self.protected_zone.is_protected(candidate.path)
                    if protection.is_protected:
                        result.skipped_paths.append((candidate.path, protection.reason))
                        stats.skipped += 1
                        logger.warning(
                            f"Protected path skipped: {candidate.path} - {protection.reason}"
                        )
                        continue

                # Add to manifest
                entry = self._create_manifest_entry(candidate)
                manifest.add_entry(entry)

                # Execute based on mode
                if self.mode == "dry-run":
                    # No actual deletion
                    logger.debug(f"Dry-run: {candidate.path}")
                    stats.deleted += 1

                elif self.mode == "trash":
                    # Move to trash
                    success, error = await self._delete_to_trash(candidate.path)
                    if success:
                        result.deleted_paths.append(candidate.path)
                        stats.deleted += 1
                        logger.info(f"Moved to trash: {candidate.path}")
                    else:
                        result.failed_paths.append((candidate.path, error))
                        stats.failed += 1
                        logger.error(f"Failed to trash {candidate.path}: {error}")

                elif self.mode == "permanent":
                    # Permanent deletion
                    success, error = await self._delete_permanent(candidate.path)
                    if success:
                        result.deleted_paths.append(candidate.path)
                        stats.deleted += 1
                        logger.info(f"Permanently deleted: {candidate.path}")
                    else:
                        result.failed_paths.append((candidate.path, error))
                        stats.failed += 1
                        logger.error(f"Failed to delete {candidate.path}: {error}")

                if progress_callback:
                    progress_callback(stats.deleted + stats.failed + stats.skipped, candidate)

            except Exception as e:
                error_msg = f"Error processing {candidate.path}: {e}"
                result.errors.append(error_msg)
                result.failed_paths.append((candidate.path, str(e)))
                stats.failed += 1
                logger.error(error_msg)

        stats.duration_seconds = time.time() - start_time
        result.stats = stats

        # Save manifest (except for dry-run)
        if self.mode != "dry-run":
            manifest.save()

        logger.info(
            f"Clean operation complete: {stats.deleted} deleted, "
            f"{stats.failed} failed, {stats.skipped} skipped"
        )

        return result

    def _create_manifest_entry(self, candidate: CleanCandidate) -> ManifestEntry:
        """
        Create a manifest entry from a candidate.

        Args:
            candidate: Clean candidate.

        Returns:
            ManifestEntry: Manifest entry.
        """
        # Handle both string and enum categories
        category_value = (
            candidate.category.value if hasattr(candidate.category, "value") else candidate.category
        )
        risk_value = (
            candidate.risk_level.value
            if hasattr(candidate.risk_level, "value")
            else candidate.risk_level
        )

        return ManifestEntry(
            path=str(candidate.path),
            size_bytes=candidate.size_bytes,
            hash_value=candidate.hash_value,
            mode=self.mode,
            category=category_value,
            risk_level=risk_value,
            is_directory=candidate.is_directory,
            metadata={
                "reason": candidate.reason,
                "last_accessed": candidate.last_accessed,
                "last_modified": candidate.last_modified,
            },
        )

    async def _delete_to_trash(self, path: Path) -> tuple[bool, str]:
        """
        Delete a file/directory to trash.

        Args:
            path: Path to delete.

        Returns:
            tuple[bool, str]: (success, error_message)
        """
        try:
            if path.is_dir():
                # send2trash doesn't support directories on all platforms
                # Fall back to recursive file deletion
                for item in sorted(path.rglob("*"), reverse=True):
                    if item.is_file():
                        send2trash(str(item))
                if path.exists():
                    path.rmdir()
            else:
                send2trash(str(path))
            return True, ""
        except Exception as e:
            return False, str(e)

    async def _delete_permanent(self, path: Path) -> tuple[bool, str]:
        """
        Permanently delete a file/directory.

        Args:
            path: Path to delete.

        Returns:
            tuple[bool, str]: (success, error_message)
        """
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return True, ""
        except Exception as e:
            return False, str(e)

    def clean_sync(
        self,
        candidates: list[CleanCandidate],
        progress_callback: Callable[[int, CleanCandidate], None] | None = None,
    ) -> CleanResult:
        """
        Synchronous wrapper for clean operation.

        Args:
            candidates: List of candidates to clean.
            progress_callback: Optional callback(count, candidate).

        Returns:
            CleanResult: Complete result.
        """
        return asyncio.run(self.clean(candidates, progress_callback))

    def preview(self, candidates: list[CleanCandidate]) -> DeletionManifest:
        """
        Create a preview manifest without any deletion.

        Args:
            candidates: List of candidates.

        Returns:
            DeletionManifest: Preview manifest.
        """
        manifest = DeletionManifest(
            mode="dry-run",
            operation_id=f"preview_{int(time.time())}",
        )

        for candidate in candidates:
            # Check Protected Zone
            if self.protected_zone.enabled:
                protection = self.protected_zone.is_protected(candidate.path)
                if protection.is_protected:
                    logger.warning(f"Protected path in preview: {candidate.path}")
                    continue

            entry = self._create_manifest_entry(candidate)
            manifest.add_entry(entry)

        return manifest
