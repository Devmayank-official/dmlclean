# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Desktop notifier backend using desktop-notifier library.

Primary notification backend with:
- Native OS notifications
- Async support
- Rich notification features
- Click handlers (where supported)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from dmlclean.notifications.notifier import NotificationBackend


class DesktopNotifierBackend(NotificationBackend):
    """
    Desktop notification backend using desktop-notifier library.

    This is the primary notification backend for DMLClean,
    providing native OS notifications on Windows, macOS, and Linux.

    Features:
    - Native notification appearance
    - Async notification sending
    - Notification actions (where supported)
    - Sound support
    - Icon support

    Example:
        ```python
        backend = DesktopNotifierBackend()
        await backend.send("Title", "Message")
        ```
    """

    def __init__(self) -> None:
        """
        Initialize the desktop notifier backend.

        Attempts to import desktop_notifier. If import fails,
        the backend will be marked as unavailable.
        """
        self._available = False
        self._notifier: Any = None

        try:
            import desktop_notifier

            # Create DesktopNotifier instance
            self._notifier = desktop_notifier.DesktopNotifier()
            self._available = True
            logger.debug("DesktopNotifierBackend initialized successfully")

        except ImportError as e:
            logger.warning(f"desktop-notifier not available: {e}")
            logger.debug("DesktopNotifierBackend will fall back to plyer")
        except Exception as e:
            logger.warning(f"Failed to initialize DesktopNotifier: {e}")
            self._available = False

    @property
    def available(self) -> bool:
        """
        Check if this backend is available.

        Returns:
            bool: True if desktop-notifier is installed and working.
        """
        return self._available

    async def send(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a desktop notification asynchronously.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds (0 = persistent).

        Returns:
            bool: True if notification sent successfully.

        Example:
            ```python
            success = await backend.send(
                "Cleaning Complete",
                "Deleted 150 files (500 MB freed)"
            )
            ```
        """
        if not self._available:
            logger.debug("DesktopNotifierBackend not available, skipping")
            return False

        try:
            # Use the notifier instance to send - API is send(title, message)
            await self._notifier.send(title, message, timeout=timeout)

            logger.debug(f"Desktop notification sent: {title}")
            return True

        except NameError:
            # desktop_notifier not defined, reimport

            try:
                await self._notifier.send(title, message, timeout=timeout)
                logger.debug(f"Desktop notification sent: {title}")
                return True
            except Exception as e:
                logger.warning(f"Desktop notification failed: {e}")
                return False
        except Exception as e:
            logger.warning(f"Desktop notification failed: {e}")
            return False

    def send_sync(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a desktop notification synchronously.

        Uses DesktopNotifierSync instance.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.
        """
        try:
            # Create sync notifier instance and call send
            from desktop_notifier import DesktopNotifierSync

            notifier = DesktopNotifierSync()
            notifier.send(title, message, timeout=timeout)
            logger.debug(f"Desktop notification sent: {title}")
            return True
        except Exception as e:
            logger.warning(f"Sync desktop notification failed: {e}")
            return False

    async def send_with_actions(
        self,
        title: str,
        message: str,
        actions: list[dict[str, str]] | None = None,
        timeout: int = 5,
    ) -> bool:
        """
        Send a notification with action buttons (where supported).

        Args:
            title: Notification title.
            message: Notification message body.
            actions: List of action buttons with 'id' and 'label'.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.

        Example:
            ```python
            actions = [
                {"id": "view", "label": "View Report"},
                {"id": "dismiss", "label": "Dismiss"},
            ]
            await backend.send_with_actions(
                "Cleaning Complete",
                "Click to view report",
                actions=actions
            )
            ```
        """
        if not self._available:
            return False

        try:
            # Note: desktop-notifier action support varies by OS
            await self._notifier.send(
                title=title,
                message=message,
                timeout=timeout,
                # actions=actions  # Uncomment when desktop-notifier supports
            )

            logger.debug(f"Desktop notification with actions sent: {title}")
            return True

        except Exception as e:
            logger.warning(f"Desktop notification with actions failed: {e}")
            return False

    async def test(self) -> bool:
        """
        Test if notifications are working.

        Returns:
            bool: True if test notification sent successfully.
        """
        return await self.send(
            "DMLClean Test",
            "This is a test notification from DMLClean",
            timeout=3,
        )

    def __repr__(self) -> str:
        """Return string representation."""
        status = "available" if self._available else "unavailable"
        return f"DesktopNotifierBackend({status})"


__all__ = ["DesktopNotifierBackend"]
