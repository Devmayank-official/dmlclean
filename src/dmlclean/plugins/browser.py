"""
Browser cache cleaner plugin.

Cleans cache from Chrome, Edge, Firefox, and Safari.
Protected: Bookmarks, passwords, cookies, history, login data.
"""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar

from dmlclean.plugins.base import CleanCandidate, CleanerPlugin, RiskLevel


class BrowserPlugin(CleanerPlugin):
    """Plugin for cleaning browser cache files."""

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return "Browser cache (Chrome, Edge, Firefox, Safari)"

    @property
    def default_enabled(self) -> bool:
        return True

    # Protected paths - NEVER clean these
    PROTECTED_PATTERNS: ClassVar[list[str]] = [
        "Bookmarks",
        "Login Data",
        "Cookies",
        "Cookies-journal",
        "Passwords",
        "History",
        "Places.sqlite",  # Firefox bookmarks/history
        "formhistory.sqlite",  # Firefox form history
        "key4.db",  # Firefox passwords
        "logins.json",  # Firefox passwords
    ]

    async def scan(self, roots: list[Path]) -> AsyncGenerator[CleanCandidate, None]:  # type: ignore[override]  # Async generator
        """Scan for browser cache files."""
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
        """Scan Windows browser cache."""
        localappdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")

        cache_paths = []

        # Chrome
        if localappdata:
            chrome_base = Path(localappdata) / "Google" / "Chrome" / "User Data"
            for profile in chrome_base.glob("*"):
                if profile.is_dir():
                    cache_paths.extend(
                        [
                            profile / "Cache",
                            profile / "Code Cache",
                            profile / "GPUCache",
                            profile / "Crashpad",
                        ]
                    )

        # Edge
        if localappdata:
            edge_base = Path(localappdata) / "Microsoft" / "Edge" / "User Data"
            for profile in edge_base.glob("*"):
                if profile.is_dir():
                    cache_paths.extend(
                        [
                            profile / "Cache",
                            profile / "Code Cache",
                            profile / "GPUCache",
                        ]
                    )

        # Firefox
        if appdata:
            firefox_profiles = Path(appdata) / "Mozilla" / "Firefox" / "Profiles"
            if firefox_profiles.exists():
                for profile in firefox_profiles.iterdir():
                    if profile.is_dir():
                        cache_paths.append(profile / "cache2")
                        cache_paths.append(profile / "startupCache")
                        cache_paths.append(profile / "crashes")

        for cache_path in cache_paths:
            if cache_path.exists():
                async for candidate in self._scan_cache_dir(cache_path, "Browser cache"):
                    yield candidate

    async def _scan_macos(self) -> AsyncGenerator[CleanCandidate, None]:
        """Scan macOS browser cache."""
        home = Path.home()
        cache_paths = [
            home / "Library" / "Caches" / "Google" / "Chrome",
            home / "Library" / "Caches" / "Microsoft Edge",
            home / "Library" / "Caches" / "Firefox",
            home / "Library" / "Safari" / "Caches",
        ]

        for cache_path in cache_paths:
            if cache_path.exists():
                async for candidate in self._scan_cache_dir(cache_path, "Browser cache"):
                    yield candidate

    async def _scan_linux(self) -> AsyncGenerator[CleanCandidate, None]:
        """Scan Linux browser cache."""
        home = Path.home()
        cache_paths = [
            home / ".cache" / "google-chrome",
            home / ".cache" / "chromium",
            home / ".mozilla" / "firefox",
        ]

        for cache_path in cache_paths:
            if cache_path.exists():
                async for candidate in self._scan_cache_dir(cache_path, "Browser cache"):
                    yield candidate

    async def _scan_cache_dir(
        self,
        root: Path,
        reason: str,
    ) -> AsyncGenerator[CleanCandidate, None]:
        """Scan a browser cache directory."""
        import asyncio

        loop = asyncio.get_event_loop()

        def is_protected(path: Path) -> bool:
            """Check if path is protected."""
            path_name = path.name
            for pattern in self.PROTECTED_PATTERNS:
                if pattern.lower() in path_name.lower():
                    return True
            return False

        def sync_scan() -> list[CleanCandidate]:
            candidates = []
            try:
                for item in root.rglob("*"):
                    try:
                        if is_protected(item):
                            continue
                        if item.is_file():
                            stat = item.stat()
                            candidates.append(
                                CleanCandidate(
                                    path=item,
                                    category=self.name,
                                    size_bytes=stat.st_size,
                                    risk_level=RiskLevel.LOW,
                                    reason=reason,
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
