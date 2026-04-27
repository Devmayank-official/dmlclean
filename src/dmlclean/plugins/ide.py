"""
IDE cache cleaner plugin.

Cleans VS Code, JetBrains, and other IDE caches.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class IDEPlugin(CleanerPlugin):
    """Plugin for cleaning IDE cache files."""

    @property
    def name(self) -> str:
        return "ide"

    @property
    def description(self) -> str:
        return "IDE cache (VS Code, JetBrains, etc.)"

    @property
    def default_enabled(self) -> bool:
        return True

    # Patterns with risk levels - .idea is HIGH risk (project settings)
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("Code/Cache", RiskLevel.LOW, "VS Code cache"),
        ("Code/CachedData", RiskLevel.LOW, "VS Code cached data"),
        ("Code/GPUCache", RiskLevel.LOW, "VS Code GPU cache"),
        (".history", RiskLevel.MEDIUM, "VS Code local history"),
        ("JetBrains", RiskLevel.MEDIUM, "JetBrains global cache"),
        (".idea", RiskLevel.HIGH, "JetBrains project settings (do not clean)"),
        ("out", RiskLevel.MEDIUM, "IDE output directory"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for IDE cache files."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []

            for root in roots:
                if not root.exists():
                    continue

                try:
                    for pattern, risk, reason in self.PATTERNS:
                        for item in root.rglob(pattern if "*" in pattern else f"*{pattern}*"):
                            try:
                                if not item.is_dir() and not item.is_file():
                                    continue

                                # Skip .idea directories (HIGH risk - project settings)
                                if ".idea" in str(item):
                                    continue

                                if item.is_file():
                                    stat = item.stat()
                                    candidates.append(
                                        CleanCandidate(
                                            path=item,
                                            category=self.name,
                                            size_bytes=stat.st_size,
                                            risk_level=risk,
                                            reason=reason,
                                            last_accessed=stat.st_atime,
                                            last_modified=stat.st_mtime,
                                        )
                                    )
                                elif item.is_dir():
                                    total_size = sum(
                                        f.stat().st_size for f in item.rglob("*") if f.is_file()
                                    )
                                    stat = item.stat()
                                    candidates.append(
                                        CleanCandidate(
                                            path=item,
                                            category=self.name,
                                            size_bytes=total_size,
                                            risk_level=risk,
                                            reason=reason,
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
        """Get Windows-specific IDE cache paths."""
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        paths = []
        if appdata:
            paths.append(str(Path(appdata) / "Code" / "Cache"))
            paths.append(str(Path(appdata) / "Code" / "CachedData"))
            paths.append(str(Path(appdata) / "Code" / "GPUCache"))
            paths.append(str(Path(appdata) / "JetBrains"))
        if localappdata:
            paths.append(str(Path(localappdata) / "JetBrains"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific IDE cache paths."""
        return [
            str(Path.home() / "Library" / "Application Support" / "Code" / "Cache"),
            str(Path.home() / "Library" / "Caches" / "JetBrains"),
        ]

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific IDE cache paths."""
        return [
            str(Path.home() / ".config" / "Code" / "Cache"),
            str(Path.home() / ".cache" / "JetBrains"),
        ]
