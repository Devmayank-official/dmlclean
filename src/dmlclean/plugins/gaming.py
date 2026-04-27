"""
Gaming cache cleaner plugin.

Cleans Steam, Epic Games, NVIDIA shader caches.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class GamingPlugin(CleanerPlugin):
    """Plugin for cleaning gaming-related cache files."""

    @property
    def name(self) -> str:
        return "gaming"

    @property
    def description(self) -> str:
        return "Gaming cache (Steam, Epic Games, NVIDIA shader cache)"

    @property
    def default_enabled(self) -> bool:
        return False

    # Gaming cache patterns
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("Steam/appcache", RiskLevel.LOW, "Steam appcache"),
        ("Steam/logs", RiskLevel.LOW, "Steam logs"),
        ("Steam/shadercache", RiskLevel.LOW, "Steam shader cache"),
        ("Steam/depotcache", RiskLevel.LOW, "Steam depot cache"),
        ("EpicGamesLauncher/Saved/Logs", RiskLevel.LOW, "Epic Games logs"),
        ("EpicGamesLauncher/Saved/webcache", RiskLevel.LOW, "Epic web cache"),
        ("EpicGamesLauncher/Saved/Crashes", RiskLevel.LOW, "Epic crash reports"),
        ("NVIDIA/DXCache", RiskLevel.LOW, "NVIDIA DirectX shader cache"),
        ("NVIDIA/GLCache", RiskLevel.LOW, "NVIDIA OpenGL shader cache"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for gaming cache files."""
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
        """Get Windows-specific gaming cache paths."""
        localappdata = os.environ.get("LOCALAPPDATA", "")
        _ = os.environ.get("PROGRAMDATA", "")  # reserved for future use
        paths = []
        if localappdata:
            # Steam
            paths.append(str(Path(localappdata) / "Steam" / "appcache"))
            paths.append(str(Path(localappdata) / "Steam" / "logs"))
            paths.append(str(Path(localappdata) / "Steam" / "shadercache"))
            # Epic
            paths.append(str(Path(localappdata) / "EpicGamesLauncher" / "Saved" / "Logs"))
            paths.append(str(Path(localappdata) / "EpicGamesLauncher" / "Saved" / "webcache"))
            # NVIDIA
            paths.append(str(Path(localappdata) / "NVIDIA" / "DXCache"))
            paths.append(str(Path(localappdata) / "NVIDIA" / "GLCache"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific gaming cache paths."""
        return []  # Gaming cache less common on macOS

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific gaming cache paths."""
        return [
            str(Path.home() / ".steam" / "steam" / "appcache"),
            str(Path.home() / ".steam" / "steam" / "logs"),
            str(Path.home() / ".steam" / "steam" / "shadercache"),
        ]
