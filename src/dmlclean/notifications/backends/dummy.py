# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Dummy notification backend for DMLClean.

No-op backend for:
- Testing environments
- Disabled notifications
- Fallback when all other backends fail
"""

from __future__ import annotations

from loguru import logger

from dmlclean.notifications.notifier import NotificationBackend


class DummyBackend(NotificationBackend):
    """
    Dummy notification backend (no-op).

    This backend does nothing - it's used for:
    - Testing environments (no actual notifications)
    - When notifications are disabled in config
    - Final fallback when all other backends fail

    This backend is always available and never fails.

    Example:
        ```python
        backend = DummyBackend()
        await backend.send("Title", "Message")  # Does nothing
        ```
    """

    def __init__(self) -> None:
        """
        Initialize the dummy notification backend.

        This backend is always available.
        """
        self._available = True
        self._sent_count = 0
        logger.debug("DummyBackend initialized (no-op backend)")

    @property
    def available(self) -> bool:
        """
        Check if this backend is available.

        Returns:
            bool: Always True (dummy backend always available).
        """
        return self._available

    async def send(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Do nothing (dummy implementation).

        Args:
            title: Notification title (ignored).
            message: Notification message (ignored).
            timeout: Notification timeout (ignored).

        Returns:
            bool: Always True (simulates success).
        """
        self._sent_count += 1
        logger.debug(f"DummyBackend: Notification suppressed - '{title}': {message}")
        return True

    def send_sync(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Do nothing (dummy implementation).

        Args:
            title: Notification title (ignored).
            message: Notification message (ignored).
            timeout: Notification timeout (ignored).

        Returns:
            bool: Always True (simulates success).
        """
        return self.send(title, message, timeout)  # type: ignore[return-value]

    async def test(self) -> bool:
        """
        Test the dummy backend (always succeeds).

        Returns:
            bool: Always True.
        """
        logger.debug("DummyBackend test: Success (no-op)")
        return True

    @property
    def sent_count(self) -> int:
        """
        Get count of notifications sent (suppressed).

        Returns:
            int: Number of send() calls made.
        """
        return self._sent_count

    def reset_count(self) -> None:
        """Reset the sent count to zero."""
        self._sent_count = 0

    def __repr__(self) -> str:
        """Return string representation."""
        return f"DummyBackend(sent={self._sent_count})"


__all__ = ["DummyBackend"]
