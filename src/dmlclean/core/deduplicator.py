"""
Deduplicator for finding duplicate files using xxhash.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from dmlclean.utils.hashing import hash_file


@dataclass
class DuplicateGroup:
    """
    A group of duplicate files.

    Attributes:
        hash_value: Common hash of all files in group.
        size_bytes: Size of each file (all same size).
        files: List of file paths with this hash.
        wasted_bytes: Space wasted by duplicates (size * (count - 1)).
    """

    hash_value: str
    size_bytes: int
    files: list[Path] = field(default_factory=list)
    wasted_bytes: int = 0

    def __post_init__(self) -> None:
        """Calculate wasted bytes."""
        self.wasted_bytes = self.size_bytes * (len(self.files) - 1) if len(self.files) > 1 else 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hash_value": self.hash_value,
            "size_bytes": self.size_bytes,
            "size_human": self._humanize_size(self.size_bytes),
            "files": [str(f) for f in self.files],
            "count": len(self.files),
            "wasted_bytes": self.wasted_bytes,
            "wasted_human": self._humanize_size(self.wasted_bytes),
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
class DeduplicationResult:
    """
    Result of duplicate detection.

    Attributes:
        groups: List of duplicate groups.
        total_duplicates: Total number of duplicate files.
        total_wasted_bytes: Total wasted space.
        files_scanned: Number of files scanned.
    """

    groups: list[DuplicateGroup] = field(default_factory=list)
    total_duplicates: int = 0
    total_wasted_bytes: int = 0
    files_scanned: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "groups": [g.to_dict() for g in self.groups],
            "total_duplicates": self.total_duplicates,
            "total_wasted_bytes": self.total_wasted_bytes,
            "total_wasted_human": self._humanize_size(self.total_wasted_bytes),
            "files_scanned": self.files_scanned,
            "duplicate_groups": len(self.groups),
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


class Deduplicator:
    """
    Duplicate file detector using xxhash.

    Uses a two-phase approach:
    1. Group files by size (quick filter)
    2. Hash files with matching sizes

    Attributes:
        algorithm: Hash algorithm to use.
        min_size: Minimum file size to consider.
    """

    def __init__(
        self,
        algorithm: str = "xxh64",
        min_size: int = 1,
    ) -> None:
        """
        Initialize the deduplicator.

        Args:
            algorithm: Hash algorithm ('xxh32', 'xxh64', 'xxh3_64', 'xxh128').
            min_size: Minimum file size in bytes to consider.
        """
        self.algorithm = algorithm
        self.min_size = min_size
        logger.debug(f"Deduplicator initialized: algorithm={algorithm}, min_size={min_size}")

    def find_duplicates(
        self,
        paths: list[Path],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> DeduplicationResult:
        """
        Find duplicate files in a list of paths.

        Args:
            paths: List of file paths to scan.
            progress_callback: Optional callback(current, total).

        Returns:
            DeduplicationResult: Result with duplicate groups.
        """
        # Phase 1: Group by size
        size_groups: dict[int, list[Path]] = defaultdict(list)
        files_scanned = 0

        for path in paths:
            try:
                if not path.is_file():
                    continue

                size = path.stat().st_size
                if size < self.min_size:
                    continue

                size_groups[size].append(path)
                files_scanned += 1

                if progress_callback:
                    progress_callback(files_scanned, len(paths))

            except OSError as e:
                logger.warning(f"Error accessing {path}: {e}")

        # Phase 2: Hash files with matching sizes
        hash_groups: dict[tuple[int, str], list[Path]] = defaultdict(list)

        for size, files in size_groups.items():
            if len(files) < 2:
                continue  # No duplicates possible

            for path in files:
                try:
                    hash_value = hash_file(path, self.algorithm)
                    hash_groups[(size, hash_value)].append(path)

                    if progress_callback:
                        progress_callback(files_scanned + 1, len(paths))

                except OSError as e:
                    logger.warning(f"Error hashing {path}: {e}")

        # Build result
        result = DeduplicationResult(files_scanned=files_scanned)

        for (size, hash_value), files in hash_groups.items():
            if len(files) < 2:
                continue  # Not a duplicate group

            group = DuplicateGroup(
                hash_value=hash_value,
                size_bytes=size,
                files=files,
            )
            result.groups.append(group)
            result.total_duplicates += len(files) - 1  # All but one are "wasted"
            result.total_wasted_bytes += group.wasted_bytes

        # Sort groups by wasted space (largest first)
        result.groups.sort(key=lambda g: g.wasted_bytes, reverse=True)

        logger.info(
            f"Deduplication complete: {len(result.groups)} groups, "
            f"{result.total_duplicates} duplicates, "
            f"{result._humanize_size(result.total_wasted_bytes)} wasted"
        )

        return result

    def find_duplicates_in_directory(
        self,
        root: Path,
        recursive: bool = True,
    ) -> DeduplicationResult:
        """
        Find duplicates in a directory.

        Args:
            root: Root directory to scan.
            recursive: Whether to scan recursively.

        Returns:
            DeduplicationResult: Result with duplicate groups.
        """
        if recursive:
            paths = list(root.rglob("*"))
        else:
            paths = list(root.glob("*"))

        return self.find_duplicates(paths)
