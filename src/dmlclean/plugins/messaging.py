"""
Messaging apps cache cleaner plugin.

Cleans Discord, Telegram, Zoom, Teams caches.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class MessagingPlugin(CleanerPlugin):
    """Plugin for cleaning messaging apps cache files."""

    @property
    def name(self) -> str:
        return "messaging"

    @property
    def description(self) -> str:
        return "Messaging cache (Discord, Telegram, Zoom, Teams)"

    @property
    def default_enabled(self) -> bool:
        return False

    # Messaging cache patterns
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("Discord/Cache", RiskLevel.LOW, "Discord cache"),
        ("Discord/Code Cache", RiskLevel.LOW, "Discord code cache"),
        ("Discord/GPUCache", RiskLevel.LOW, "Discord GPU cache"),
        ("Discord/Cache Cache", RiskLevel.LOW, "Discord service worker cache"),
        ("Telegram Desktop/tdata/temp", RiskLevel.LOW, "Telegram temp data"),
        ("Zoom/logs", RiskLevel.LOW, "Zoom logs"),
        ("Microsoft/Teams/Cache", RiskLevel.LOW, "Microsoft Teams cache"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for messaging cache files."""
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
        """Get Windows-specific messaging cache paths."""
        appdata = os.environ.get("APPDATA", "")
        _ = os.environ.get("LOCALAPPDATA", "")  # reserved for future use
        paths = []
        if appdata:
            paths.append(str(Path(appdata) / "Discord" / "Cache"))
            paths.append(str(Path(appdata) / "Discord" / "Code Cache"))
            paths.append(str(Path(appdata) / "Telegram Desktop" / "tdata" / "temp"))
            paths.append(str(Path(appdata) / "Zoom" / "logs"))
            paths.append(str(Path(appdata) / "Microsoft" / "Teams" / "Cache"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific messaging cache paths."""
        return [
            str(Path.home() / "Library" / "Application Support" / "Discord" / "Cache"),
        ]

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific messaging cache paths."""
        return [
            str(Path.home() / ".config" / "Discord" / "Cache"),
        ]
