"""
Cloud sync cache cleaner plugin.

Cleans OneDrive, Google Drive, Dropbox caches.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class CloudSyncPlugin(CleanerPlugin):
    """Plugin for cleaning cloud sync cache files."""

    @property
    def name(self) -> str:
        return "cloud_sync"

    @property
    def description(self) -> str:
        return "Cloud sync cache (OneDrive, Google Drive, Dropbox)"

    @property
    def default_enabled(self) -> bool:
        return False

    # Cloud sync cache patterns
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("OneDrive/logs", RiskLevel.LOW, "OneDrive logs"),
        ("OneDrive/temp", RiskLevel.LOW, "OneDrive temp files"),
        ("Google/DriveFS", RiskLevel.MEDIUM, "Google Drive file stream cache"),
        ("Dropbox/cache", RiskLevel.LOW, "Dropbox cache"),
        ("Dropbox/.dropbox.cache", RiskLevel.LOW, "Dropbox cache file"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for cloud sync cache files."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []

            for root in roots:
                if not root.exists():
                    continue

                try:
                    for pattern, risk, reason in self.PATTERNS:
                        pattern_path = root / pattern
                        if pattern_path.exists():
                            if pattern_path.is_file():
                                try:
                                    stat = pattern_path.stat()
                                    candidates.append(
                                        CleanCandidate(
                                            path=pattern_path,
                                            category=self.name,
                                            size_bytes=stat.st_size,
                                            risk_level=risk,
                                            reason=reason,
                                            last_accessed=stat.st_atime,
                                            last_modified=stat.st_mtime,
                                        )
                                    )
                                except (OSError, PermissionError):
                                    pass
                            elif pattern_path.is_dir():
                                total_size = 0
                                file_count = 0
                                for f in pattern_path.rglob("*"):
                                    if f.is_file():
                                        try:
                                            total_size += f.stat().st_size
                                            file_count += 1
                                        except OSError:
                                            pass

                                try:
                                    stat = pattern_path.stat()
                                    candidates.append(
                                        CleanCandidate(
                                            path=pattern_path,
                                            category=self.name,
                                            size_bytes=total_size,
                                            risk_level=risk,
                                            reason=f"{reason} ({file_count} files)",
                                            last_accessed=stat.st_atime,
                                            last_modified=stat.st_mtime,
                                            is_directory=True,
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

    def get_windows_paths(self) -> list[str]:
        """Get Windows-specific cloud sync cache paths."""
        localappdata = os.environ.get("LOCALAPPDATA", "")
        os.environ.get("APPDATA", "")
        paths = []
        if localappdata:
            paths.append(str(Path(localappdata) / "Microsoft" / "OneDrive" / "logs"))
            paths.append(str(Path(localappdata) / "Google" / "DriveFS"))
            paths.append(str(Path(localappdata) / "Dropbox" / "cache"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific cloud sync cache paths."""
        return []

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific cloud sync cache paths."""
        return []
