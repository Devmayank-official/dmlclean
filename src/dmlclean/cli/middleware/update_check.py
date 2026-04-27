"""
Update Check Middleware for DMLClean.

Provides background PyPI version checking with:
- Non-blocking HTTP request
- Update notification on new version available
- Configurable check interval
- Graceful failure on network errors
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console

from dmlclean import __version__


@dataclass
class VersionInfo:
    """Version information from PyPI."""

    latest_version: str
    current_version: str
    release_date: str
    download_url: str
    is_newer: bool

    @classmethod
    def from_pypi_response(cls, data: dict[str, Any], current_version: str) -> VersionInfo:
        """Create VersionInfo from PyPI API response."""
        latest = data.get("info", {}).get("version", "0.0.0")
        release_info = data.get("releases", {}).get(latest, [{}])
        release_date = release_info[0].get("upload_time_iso_8601", "")[:10] if release_info else ""

        return cls(
            latest_version=latest,
            current_version=current_version,
            release_date=release_date,
            download_url="https://pypi.org/project/dmlclean/",
            is_newer=cls._version_greater_than(latest, current_version),
        )

    @staticmethod
    def _version_greater_than(v1: str, v2: str) -> bool:
        """Check if v1 > v2."""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            return parts1 > parts2
        except (ValueError, AttributeError):
            return False


@dataclass
class CheckState:
    """State for update checking."""

    last_check: datetime | None = None
    latest_version: str | None = None
    check_interval_hours: int = 24
    cache_file: Path | None = None


class UpdateCheckMiddleware:
    """
    Background update checker for DMLClean.

    Checks PyPI for new versions and displays notification
    if update is available.

    Usage:
        ```python
        # Register at app startup
        UpdateCheckMiddleware.register(console)

        # Or check manually
        middleware = UpdateCheckMiddleware(console)
        await middleware.check_for_updates()
        ```
    """

    PYPI_URL = "https://pypi.org/pypi/dmlclean/json"
    CHECK_INTERVAL = timedelta(hours=24)

    def __init__(
        self,
        console: Console,
        check_interval_hours: int = 24,
        timeout_seconds: float = 3.0,
    ) -> None:
        """
        Initialize update checker.

        Args:
            console: Rich console for output.
            check_interval_hours: Hours between checks (default: 24).
            timeout_seconds: HTTP request timeout (default: 3.0).
        """
        self.console = console
        self.check_interval = timedelta(hours=check_interval_hours)
        self.timeout = timeout_seconds
        self._state = CheckState()
        self._task: asyncio.Task | None = None

    @classmethod
    def register(
        cls,
        console: Console,
        check_interval_hours: int = 24,
    ) -> UpdateCheckMiddleware:
        """
        Register update checker.

        Args:
            console: Rich console for output.
            check_interval_hours: Hours between checks.

        Returns:
            UpdateCheckMiddleware: Registered middleware instance.
        """
        middleware = cls(console, check_interval_hours)
        middleware._start_background_check()
        return middleware

    def _start_background_check(self) -> None:
        """Start non-blocking background version check."""
        try:
            loop = asyncio.get_event_loop()
            self._task = loop.create_task(self._check_update_async())
        except RuntimeError:
            # No event loop, skip async check
            pass

    async def _check_update_async(self) -> None:
        """Async update check with timeout."""
        try:
            await asyncio.wait_for(self._fetch_and_notify(), timeout=self.timeout)
        except TimeoutError:
            pass  # Silently ignore timeout
        except Exception:
            pass  # Silently ignore errors

    async def _fetch_and_notify(self) -> None:
        """Fetch version from PyPI and notify if update available."""
        # Check if we should skip (recent check)
        if self._state.last_check:
            elapsed = datetime.now() - self._state.last_check
            if elapsed < self.check_interval:
                return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.PYPI_URL, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()

            version_info = VersionInfo.from_pypi_response(data, __version__)

            if version_info.is_newer:
                self._show_update_notification(version_info)

            # Update state
            self._state.last_check = datetime.now()
            self._state.latest_version = version_info.latest_version

        except Exception:
            # Silently ignore all errors (network, parsing, etc.)
            pass

    def _show_update_notification(self, version_info: VersionInfo) -> None:
        """
        Show update available notification.

        Args:
            version_info: Version information.
        """
        from rich.panel import Panel

        message = (
            f"New version available: [green]{version_info.latest_version}[/green]\n\n"
            f"Current version: [dim]{__version__}[/dim]\n"
            f"Released: {version_info.release_date}\n\n"
            f"Update with:\n"
            f"[bold]pip install --upgrade dmlclean[/bold]\n\n"
            f"[dim]Download: {version_info.download_url}[/dim]"
        )

        self.console.print(
            Panel(
                message,
                title="[bold blue]📦 Update Available[/bold blue]",
                border_style="blue",
            )
        )

    async def check_for_updates(self) -> VersionInfo | None:
        """
        Manually check for updates.

        Returns:
            VersionInfo | None: Version info if update available, None otherwise.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.PYPI_URL, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()

            version_info = VersionInfo.from_pypi_response(data, __version__)

            if version_info.is_newer:
                self._show_update_notification(version_info)

            self._state.last_check = datetime.now()
            self._state.latest_version = version_info.latest_version

            return version_info if version_info.is_newer else None

        except Exception:
            return None

    def check_for_updates_sync(self) -> VersionInfo | None:
        """
        Synchronous wrapper for update check.

        Returns:
            VersionInfo | None: Version info if update available.
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.check_for_updates())
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.check_for_updates())

    def get_current_version(self) -> str:
        """Get current version."""
        return __version__

    def get_latest_version(self) -> str | None:
        """Get cached latest version."""
        return self._state.latest_version

    def has_update(self) -> bool:
        """Check if update is available (from cache)."""
        if not self._state.latest_version:
            return False
        return VersionInfo._version_greater_than(self._state.latest_version, __version__)


__all__ = ["UpdateCheckMiddleware", "VersionInfo"]
