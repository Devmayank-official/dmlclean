"""
System junk cleaner plugin.

Cleans OS temporary files, logs, crash reports, and other system junk.
"""

from __future__ import annotations

# ruff: noqa: S108  # reason: cleaning tool legitimately works with temp dirs
import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class SystemJunkPlugin(CleanerPlugin):
    """Plugin for cleaning system temporary files and junk."""

    @property
    def name(self) -> str:
        return "system_junk"

    @property
    def description(self) -> str:
        return "System temporary files, logs, crash reports, and junk"

    @property
    def default_enabled(self) -> bool:
        return True

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for system junk files."""

        if sys.platform == "win32":
            async for candidate in self._scan_windows():
                yield candidate
        elif sys.platform == "darwin":
            async for candidate in self._scan_macos():
                yield candidate
        else:
            async for candidate in self._scan_linux():
                yield candidate

    async def _scan_windows(self) -> AsyncGenerator[CleanCandidate, None]:
        """Scan Windows-specific temp files."""
        temp_dirs = [
            os.environ.get("TEMP", "C:\\Windows\\Temp"),
            os.environ.get("TMP", "C:\\Windows\\Temp"),
            os.environ.get("LOCALAPPDATA", "") + "\\Temp",
        ]

        for temp_dir in temp_dirs:
            if not temp_dir:
                continue
            path = Path(temp_dir)
            if path.exists():
                async for candidate in self._scan_directory(path, "Windows temp"):
                    yield candidate

    async def _scan_macos(self) -> AsyncGenerator[CleanCandidate, None]:
        """Scan macOS-specific temp files."""
        temp_dirs = [
            Path.home() / "Library" / "Logs",
            Path("/tmp"),  # intentional: scanning temp dirs
            Path("/var/tmp"),  # intentional: scanning temp dirs
        ]

        for temp_dir in temp_dirs:
            if temp_dir.exists():
                async for candidate in self._scan_directory(temp_dir, "macOS temp/logs"):
                    yield candidate

    async def _scan_linux(self) -> AsyncGenerator[CleanCandidate, None]:
        """Scan Linux-specific temp files."""
        temp_dirs = [
            Path("/tmp"),  # intentional: scanning temp dirs
            Path("/var/tmp"),  # intentional: scanning temp dirs
            Path.home() / ".cache",
        ]

        for temp_dir in temp_dirs:
            if temp_dir.exists():
                async for candidate in self._scan_directory(temp_dir, "Linux temp/cache"):
                    yield candidate

    async def _scan_directory(
        self,
        root: Path,
        category_name: str,
    ) -> AsyncGenerator[CleanCandidate, None]:
        """Recursively scan a directory for cleanable files."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []
            try:
                for item in root.rglob("*"):
                    try:
                        if item.is_file():
                            stat = item.stat()
                            candidates.append(
                                CleanCandidate(
                                    path=item,
                                    category=self.name,
                                    size_bytes=stat.st_size,
                                    risk_level=RiskLevel.LOW,
                                    reason=category_name,
                                    last_accessed=stat.st_atime,
                                    last_modified=stat.st_mtime,
                                )
                            )
                    except (OSError, PermissionError):
                        continue
            except (OSError, PermissionError):
                pass
            return candidates

        candidates = await loop.run_in_executor(None, sync_scan)
        for candidate in candidates:
            yield candidate
