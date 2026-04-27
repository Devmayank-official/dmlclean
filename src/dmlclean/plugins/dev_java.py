"""
Java/Maven/Gradle artifacts cleaner plugin.

Cleans build outputs, caches, and compiled class files.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class JavaDevPlugin(CleanerPlugin):
    """Plugin for cleaning Java/Gradle/Maven development artifacts."""

    @property
    def name(self) -> str:
        return "dev_java"

    @property
    def description(self) -> str:
        return "Java/Gradle/Maven build artifacts and caches"

    @property
    def default_enabled(self) -> bool:
        return False  # Opt-in for development environments

    # Patterns with risk levels and reasons
    PATTERNS: ClassVar[list[tuple[str, RiskLevel, str]]] = [
        ("build", RiskLevel.MEDIUM, "Gradle build output"),
        (".gradle", RiskLevel.MEDIUM, "Gradle cache"),
        ("target", RiskLevel.MEDIUM, "Maven target directory"),
        ("*.class", RiskLevel.LOW, "Compiled Java class file"),
        (".m2", RiskLevel.HIGH, "Maven local repository (large, re-download expensive)"),
        (".idea", RiskLevel.HIGH, "JetBrains project settings (do not clean by default)"),
        ("out", RiskLevel.MEDIUM, "IDE output directory"),
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for Java development artifacts."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []

            for root in roots:
                if not root.exists():
                    continue

                try:
                    for pattern, risk, reason in self.PATTERNS:
                        if pattern.startswith("*."):
                            for item in root.rglob(pattern):
                                try:
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
                                except (OSError, PermissionError):
                                    pass
                        else:
                            for item in root.rglob(pattern):
                                try:
                                    if not item.is_dir():
                                        continue

                                    # Special handling for .m2 repository - HIGH risk
                                    if pattern == ".m2":
                                        # Only flag if it's the global Maven repo
                                        if not str(item).endswith(".m2"):
                                            continue

                                    # Calculate directory size
                                    total_size = 0
                                    file_count = 0
                                    try:
                                        for f in item.rglob("*"):
                                            if f.is_file():
                                                try:
                                                    total_size += f.stat().st_size
                                                    file_count += 1
                                                except OSError:
                                                    pass
                                    except OSError:
                                        pass

                                    stat = item.stat()
                                    candidates.append(
                                        CleanCandidate(
                                            path=item,
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
        """Get Windows-specific Java cache paths."""
        userprofile = os.environ.get("USERPROFILE", "")
        paths = []
        if userprofile:
            paths.append(str(Path(userprofile) / ".gradle" / "caches"))
            paths.append(str(Path(userprofile) / ".m2" / "repository"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific Java cache paths."""
        return [
            str(Path.home() / ".gradle" / "caches"),
            str(Path.home() / ".m2" / "repository"),
        ]

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific Java cache paths."""
        return [
            str(Path.home() / ".gradle" / "caches"),
            str(Path.home() / ".m2" / "repository"),
        ]
