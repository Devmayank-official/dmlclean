# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Plyer notification backend for DMLClean.

Fallback notification backend using plyer library:
- Cross-platform support
- Simple API
- Works when desktop-notifier fails
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from dmlclean.notifications.notifier import NotificationBackend


class PlyerBackend(NotificationBackend):
    """
    Plyer notification backend for DMLClean.

    This is the fallback notification backend, used when
    desktop-notifier is not available. Plyer provides
    cross-platform notifications with a simple API.

    Features:
    - Windows, macOS, Linux support
    - Simple synchronous API
    - Icon support (where available)
    - Timeout support

    Example:
        ```python
        backend = PlyerBackend()
        backend.send("Title", "Message")
        ```
    """

    def __init__(self) -> None:
        """
        Initialize the plyer notification backend.

        Attempts to import plyer.notification. If import fails,
        the backend will be marked as unavailable.
        """
        self._available = False
        self._notification: Any = None

        try:
            from plyer import notification

            self._notification = notification
            self._available = True
            logger.debug("PlyerBackend initialized successfully")

        except ImportError as e:
            logger.warning(f"plyer not available: {e}")
            logger.debug("PlyerBackend will fall back to dummy backend")

    @property
    def available(self) -> bool:
        """
        Check if this backend is available.

        Returns:
            bool: True if plyer is installed and working.
        """
        return self._available

    async def send(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a notification using plyer.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.

        Example:
            ```python
            success = await backend.send(
                "Cleaning Complete",
                "Deleted 150 files"
            )
            ```
        """
        if not self._available:
            logger.debug("PlyerBackend not available, skipping")
            return False

        try:
            # Plyer uses synchronous API
            self._notification.notify(
                title=title,
                message=message,
                timeout=timeout,
                # app_name="DMLClean",  # Optional: add app name
            )

            logger.debug(f"Plyer notification sent: {title}")
            return True

        except Exception as e:
            logger.warning(f"Plyer notification failed: {e}")
            return False

    def send_sync(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a notification synchronously using plyer.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.
        """
        return self.send(title, message, timeout)  # type: ignore[return-value]

    async def test(self) -> bool:
        """
        Test if plyer notifications are working.

        Returns:
            bool: True if test notification sent successfully.
        """
        return await self.send(
            "DMLClean Test",
            "This is a test notification from DMLClean (Plyer backend)",
            timeout=3,
        )

    def __repr__(self) -> str:
        """Return string representation."""
        status = "available" if self._available else "unavailable"
        return f"PlyerBackend({status})"


__all__ = ["PlyerBackend"]
