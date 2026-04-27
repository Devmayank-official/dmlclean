"""
Smart scan plugin.

Finds large files, old/stale files, duplicates, empty directories, and broken symlinks.
"""

from __future__ import annotations

# reason: cleaning tool legitimately works with temp dirs
import time
from collections.abc import AsyncGenerator
from pathlib import Path

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class SmartScanPlugin(CleanerPlugin):
    """Plugin for smart scanning - large files, old files, duplicates,
    empty dirs, broken symlinks."""

    @property
    def name(self) -> str:
        return "smart_scan"

    @property
    def description(self) -> str:
        return "Smart scan (large files, old files, empty dirs, broken symlinks)"

    @property
    def default_enabled(self) -> bool:
        return True

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for smart scan candidates."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []
            large_file_threshold_mb = 500
            stale_file_days = 90

            for root in roots:
                if not root.exists():
                    continue

                try:
                    # Scan all files
                    for item in root.rglob("*"):
                        try:
                            # Skip protected paths
                            if self._is_protected(item):
                                continue

                            if item.is_file():
                                stat = item.stat()

                                # Large files
                                size_mb = stat.st_size / (1024 * 1024)
                                if size_mb >= large_file_threshold_mb:
                                    candidates.append(
                                        CleanCandidate(
                                            path=item,
                                            category=self.name,
                                            size_bytes=stat.st_size,
                                            risk_level=RiskLevel.MEDIUM,
                                            reason=f"Large file ({size_mb:.1f} MB)",
                                            last_accessed=stat.st_atime,
                                            last_modified=stat.st_mtime,
                                            metadata={"size_mb": size_mb},
                                        )
                                    )

                                # Old/stale files
                                age_days = (time.time() - stat.st_atime) / (24 * 60 * 60)
                                if age_days >= stale_file_days:
                                    candidates.append(
                                        CleanCandidate(
                                            path=item,
                                            category=self.name,
                                            size_bytes=stat.st_size,
                                            risk_level=RiskLevel.MEDIUM,
                                            reason=(
                                                f"Stale file (not accessed in {age_days:.0f} days)"
                                            ),
                                            last_accessed=stat.st_atime,
                                            last_modified=stat.st_mtime,
                                            metadata={"age_days": age_days},
                                        )
                                    )

                            elif item.is_dir():
                                # Empty directories
                                try:
                                    if not any(item.iterdir()):
                                        stat = item.stat()
                                        candidates.append(
                                            CleanCandidate(
                                                path=item,
                                                category=self.name,
                                                size_bytes=0,
                                                risk_level=RiskLevel.LOW,
                                                reason="Empty directory",
                                                last_accessed=stat.st_atime,
                                                last_modified=stat.st_mtime,
                                                is_directory=True,
                                            )
                                        )
                                except OSError:
                                    pass

                                # Broken symlinks (for directories)
                                if item.is_symlink():
                                    try:
                                        if not item.resolve():
                                            stat = item.stat()
                                            candidates.append(
                                                CleanCandidate(
                                                    path=item,
                                                    category=self.name,
                                                    size_bytes=0,
                                                    risk_level=RiskLevel.LOW,
                                                    reason="Broken symlink",
                                                    last_accessed=stat.st_atime,
                                                    last_modified=stat.st_mtime,
                                                    is_directory=True,
                                                )
                                            )
                                    except OSError:
                                        pass

                        except (OSError, PermissionError):
                            pass

                    # Check for broken symlinks (files)
                    for item in root.rglob("*"):
                        try:
                            if item.is_symlink() and not item.exists():
                                stat = item.lstat()
                                candidates.append(
                                    CleanCandidate(
                                        path=item,
                                        category=self.name,
                                        size_bytes=0,
                                        risk_level=RiskLevel.LOW,
                                        reason="Broken symlink",
                                        last_accessed=stat.st_atime,
                                        last_modified=stat.st_mtime,
                                    )
                                )
                        except (OSError, PermissionError):
                            pass

                except (OSError, PermissionError):
                    pass

            return candidates

        candidates = await loop.run_in_executor(None, sync_scan)
        for candidate in candidates:
            yield candidate

    def _is_protected(self, path: Path) -> bool:
        """Check if path is protected."""
        protected_patterns = [".git", "venv", ".venv", "node_modules"]
        path_str = str(path).lower()
        for pattern in protected_patterns:
            if pattern in path_str:
                return True
        return False
