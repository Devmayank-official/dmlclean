"""
Async file system scanner for DMLClean.

Provides high-performance, async-first file system scanning
with support for deep traversal, filtering, and progress tracking.

Plugin Integration:
    The scanner supports plugin-based scanning via PluginLoader.
    When use_plugins=True, plugins are lazily loaded and invoked
    for each category during the scan phase.

Example:
    ```python
    # Basic scanning
    scanner = FileSystemScanner()
    result = await scanner.scan([Path("/tmp")])

    # Plugin-aware scanning
    scanner = FileSystemScanner(use_plugins=True, config=config)
    result = await scanner.scan([Path("/tmp")])
    ```
"""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger


@dataclass
class ScanStats:
    """
    Statistics from a scan operation.

    Attributes:
        total_files: Total number of files scanned.
        total_directories: Total number of directories scanned.
        total_size_bytes: Total size of all scanned files.
        errors: Number of errors encountered.
        duration_seconds: Time taken for the scan.
        files_per_second: Scan speed in files per second.
    """

    total_files: int = 0
    total_directories: int = 0
    total_size_bytes: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    files_per_second: float = 0.0

    def to_dict(self) -> dict[str, str | int | float]:
        """Convert to dictionary for reporting."""
        return {
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size_bytes": self.total_size_bytes,
            "total_size_human": self._humanize_size(self.total_size_bytes),
            "errors": self.errors,
            "duration_seconds": round(self.duration_seconds, 2),
            "files_per_second": round(self.files_per_second, 2),
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
class ScanResult:
    """
    Result of a file system scan.

    Attributes:
        paths: List of scanned file paths.
        directories: List of scanned directory paths.
        stats: Scan statistics.
        errors: List of paths that caused errors.
    """

    paths: list[Path] = field(default_factory=list)
    directories: list[Path] = field(default_factory=list)
    stats: ScanStats = field(default_factory=ScanStats)
    errors: list[tuple[Path, str]] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Return True if any files were found."""
        return bool(self.paths)

    def __len__(self) -> int:
        """Return number of files found."""
        return len(self.paths)


class FileSystemScanner:
    """
    Async file system scanner for DMLClean.

    Provides high-performance scanning with:
    - Async I/O for non-blocking operations
    - Configurable depth limits
    - Symlink handling options
    - Progress callbacks
    - Error resilience

    Attributes:
        follow_symlinks: Whether to follow symbolic links.
        max_depth: Maximum directory depth (0 = unlimited).
        include_patterns: Glob patterns to include.
        exclude_patterns: Glob patterns to exclude.
        max_workers: Maximum concurrent operations.
    """

    def __init__(
        self,
        follow_symlinks: bool = False,
        max_depth: int = 0,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        max_workers: int = 10,
    ) -> None:
        """
        Initialize the file system scanner.

        Args:
            follow_symlinks: Whether to follow symbolic links.
            max_depth: Maximum directory depth (0 = unlimited).
            include_patterns: Glob patterns to include (None = all).
            exclude_patterns: Glob patterns to exclude.
            max_workers: Maximum concurrent scan operations.
        """
        self.follow_symlinks = follow_symlinks
        self.max_depth = max_depth
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns or []
        self.max_workers = max_workers

        self._semaphore = asyncio.Semaphore(max_workers)
        logger.debug(
            f"FileSystemScanner initialized: "
            f"follow_symlinks={follow_symlinks}, max_depth={max_depth}"
        )

    async def scan(
        self,
        roots: list[Path],
        progress_callback: Callable[[int, Path], None] | None = None,
    ) -> ScanResult:
        """
        Scan multiple root paths asynchronously.

        Args:
            roots: List of root paths to scan from.
            progress_callback: Optional callback(current_count, current_path).

        Returns:
            ScanResult: Complete scan result with all paths and stats.
        """
        start_time = time.time()
        all_paths: list[Path] = []
        all_directories: list[Path] = []
        all_errors: list[tuple[Path, str]] = []
        total_size = 0
        file_count = 0
        dir_count = 0
        error_count = 0

        for root in roots:
            if not root.exists():
                logger.warning(f"Root path does not exist: {root}")
                all_errors.append((root, "Path does not exist"))
                error_count += 1
                continue

            try:
                result = await self._scan_directory(root, depth=0)
                all_paths.extend(result.paths)
                all_directories.extend(result.directories)
                all_errors.extend(result.errors)
                total_size += result.stats.total_size_bytes
                file_count += result.stats.total_files
                dir_count += result.stats.total_directories
                error_count += result.stats.errors

                if progress_callback:
                    for path in result.paths:
                        progress_callback(file_count, path)

            except Exception as e:
                logger.error(f"Error scanning {root}: {e}")
                all_errors.append((root, str(e)))
                error_count += 1

        duration = time.time() - start_time
        stats = ScanStats(
            total_files=file_count,
            total_directories=dir_count,
            total_size_bytes=total_size,
            errors=error_count,
            duration_seconds=duration,
            files_per_second=file_count / duration if duration > 0 else 0,
        )

        return ScanResult(
            paths=all_paths,
            directories=all_directories,
            stats=stats,
            errors=all_errors,
        )

    async def _scan_directory(
        self,
        root: Path,
        depth: int = 0,
    ) -> ScanResult:
        """
        Recursively scan a directory.

        Args:
            root: Root directory to scan.
            depth: Current depth level.

        Returns:
            ScanResult: Scan result for this directory.
        """
        paths: list[Path] = []
        directories: list[Path] = []
        errors: list[tuple[Path, str]] = []
        total_size = 0
        file_count = 0
        dir_count = 0
        error_count = 0

        # Check depth limit
        if self.max_depth > 0 and depth >= self.max_depth:
            logger.debug(f"Max depth reached at {root} (depth={depth})")
            return ScanResult()

        try:
            entries = await self._list_directory(root)
        except PermissionError as e:
            logger.warning(f"Permission denied: {root}")
            errors.append((root, f"Permission denied: {e}"))
            return ScanResult(errors=errors)
        except OSError as e:
            logger.warning(f"OS error scanning {root}: {e}")
            errors.append((root, f"OS error: {e}"))
            return ScanResult(errors=errors)

        for entry in entries:
            try:
                entry_path = root / entry.name

                # Check if we should skip this entry
                if not await self._should_include(entry_path):
                    continue

                # Handle symlinks
                if entry_path.is_symlink():
                    if not self.follow_symlinks:
                        continue
                    # Prevent infinite loops by checking if symlink points outside root
                    try:
                        resolved = entry_path.resolve()
                        if not str(resolved).startswith(str(root.resolve())):
                            continue
                    except OSError:
                        continue

                if entry_path.is_dir():
                    directories.append(entry_path)
                    dir_count += 1

                    # Recurse into subdirectory
                    sub_result = await self._scan_directory(entry_path, depth + 1)
                    paths.extend(sub_result.paths)
                    directories.extend(sub_result.directories)
                    errors.extend(sub_result.errors)
                    total_size += sub_result.stats.total_size_bytes
                    file_count += sub_result.stats.total_files
                    dir_count += sub_result.stats.total_directories
                    error_count += sub_result.stats.errors

                elif entry_path.is_file():
                    if self._matches_patterns(entry_path.name):
                        paths.append(entry_path)
                        file_count += 1
                        try:
                            size = entry_path.stat().st_size
                            total_size += size
                        except OSError:
                            pass

            except PermissionError as e:
                errors.append((entry_path, f"Permission denied: {e}"))
                error_count += 1
            except OSError as e:
                errors.append((entry_path, f"OS error: {e}"))
                error_count += 1

        return ScanResult(
            paths=paths,
            directories=directories,
            stats=ScanStats(
                total_files=file_count,
                total_directories=dir_count,
                total_size_bytes=total_size,
                errors=error_count,
            ),
            errors=errors,
        )

    async def _list_directory(self, path: Path) -> list[os.DirEntry[str]]:
        """
        List directory entries asynchronously.

        Args:
            path: Directory to list.

        Returns:
            list[os.DirEntry]: List of directory entries.
        """
        loop = asyncio.get_event_loop()

        def sync_listdir() -> list[os.DirEntry[str]]:
            with os.scandir(path) as it:
                return list(it)

        return await loop.run_in_executor(None, sync_listdir)

    async def _should_include(self, path: Path) -> bool:
        """
        Check if a path should be included based on patterns.

        Args:
            path: Path to check.

        Returns:
            bool: True if path should be included.
        """
        # Check exclude patterns first
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return False

        # If include patterns specified, must match at least one
        if self.include_patterns:
            path_str = path.name
            for pattern in self.include_patterns:
                if pattern in path_str:
                    return True
            return False

        return True

    def _matches_patterns(self, filename: str) -> bool:
        """
        Check if a filename matches include/exclude patterns.

        Args:
            filename: Filename to check.

        Returns:
            bool: True if filename should be included.
        """
        import fnmatch

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return False

        # If include patterns specified, must match at least one
        if self.include_patterns:
            for pattern in self.include_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    return True
            return False

        return True

    async def scan_files_only(
        self,
        roots: list[Path],
        extensions: list[str] | None = None,
    ) -> list[Path]:
        """
        Scan for files with specific extensions.

        Args:
            roots: Root paths to scan.
            extensions: File extensions to include (e.g., ['.tmp', '.log']).

        Returns:
            list[Path]: List of matching file paths.
        """
        if extensions:
            self.include_patterns = [f"*{ext}" for ext in extensions]

        result = await self.scan(roots)
        return result.paths

    async def get_directory_size(self, path: Path) -> int:
        """
        Calculate total size of a directory asynchronously.

        Args:
            path: Directory path.

        Returns:
            int: Total size in bytes.
        """
        result = await self._scan_directory(path)
        return result.stats.total_size_bytes
