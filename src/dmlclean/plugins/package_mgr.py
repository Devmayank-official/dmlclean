"""
Package manager cache cleaner plugin.

Cleans pip, npm, apt, dnf, pacman, brew caches.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class PackageManagerPlugin(CleanerPlugin):
    """Plugin for cleaning package manager cache files."""

    @property
    def name(self) -> str:
        return "package_manager"

    @property
    def description(self) -> str:
        return "Package manager cache (pip, npm, apt, dnf, pacman, brew)"

    @property
    def default_enabled(self) -> bool:
        return False

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for package manager cache files."""
        import asyncio

        loop = asyncio.get_event_loop()

        def sync_scan() -> list[CleanCandidate]:
            candidates = []

            for root in roots:
                if not root.exists():
                    continue

                try:
                    # pip cache
                    for pip_cache in root.rglob("*pip*cache*"):
                        if pip_cache.is_dir():
                            total_size = sum(
                                f.stat().st_size for f in pip_cache.rglob("*") if f.is_file()
                            )
                            if total_size > 0:
                                stat = pip_cache.stat()
                                candidates.append(
                                    CleanCandidate(
                                        path=pip_cache,
                                        category=self.name,
                                        size_bytes=total_size,
                                        risk_level=RiskLevel.LOW,
                                        reason="pip cache",
                                        last_accessed=stat.st_atime,
                                        last_modified=stat.st_mtime,
                                        is_directory=True,
                                    )
                                )

                    # npm cache
                    for npm_cache in root.rglob("*npm-cache*"):
                        if npm_cache.is_dir():
                            total_size = sum(
                                f.stat().st_size for f in npm_cache.rglob("*") if f.is_file()
                            )
                            if total_size > 0:
                                stat = npm_cache.stat()
                                candidates.append(
                                    CleanCandidate(
                                        path=npm_cache,
                                        category=self.name,
                                        size_bytes=total_size,
                                        risk_level=RiskLevel.LOW,
                                        reason="npm cache",
                                        last_accessed=stat.st_atime,
                                        last_modified=stat.st_mtime,
                                        is_directory=True,
                                    )
                                )

                except (OSError, PermissionError):
                    pass

            return candidates

        candidates = await loop.run_in_executor(None, sync_scan)
        for candidate in candidates:
            yield candidate

    def get_windows_paths(self) -> list[str]:
        """Get Windows-specific package manager cache paths."""
        localappdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        paths = []
        if localappdata:
            paths.append(str(Path(localappdata) / "pip" / "Cache"))
            paths.append(str(Path(localappdata) / "npm-cache"))
        if appdata:
            paths.append(str(Path(appdata) / "npm-cache"))
        return paths

    def get_macos_paths(self) -> list[str]:
        """Get macOS-specific package manager cache paths."""
        paths = [
            str(Path.home() / ".cache" / "pip"),
            str(Path.home() / ".npm"),
        ]
        # Homebrew cache
        try:
            result = subprocess.run(
                ["brew", "--cache"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                paths.append(result.stdout.strip())
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        return paths

    def get_linux_paths(self) -> list[str]:
        """Get Linux-specific package manager cache paths."""
        return [
            str(Path.home() / ".cache" / "pip"),
            str(Path.home() / ".npm"),
            "/var/cache/apt/archives",
            "/var/cache/dnf",
            "/var/cache/pacman/pkg",
        ]
