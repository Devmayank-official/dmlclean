# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Main notification dispatcher for DMLClean.

Provides unified notification API with:
- Automatic backend selection (layered approach)
- Async and sync support
- Configuration-driven behavior
- Graceful degradation
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from dmlclean.config.schema import NotificationsConfig


class NotificationBackend(ABC):
    """
    Abstract base class for notification backends.

    All notification backends must implement this interface.
    Backends are tried in order until one succeeds.

    Example:
        ```python
        class CustomBackend(NotificationBackend):
            async def send(self, title, message, timeout):
                # Custom implementation
                return True
        ```
    """

    @property
    @abstractmethod
    def available(self) -> bool:
        """
        Check if this backend is available.

        Returns:
            bool: True if backend can send notifications.
        """
        pass

    @abstractmethod
    async def send(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a notification asynchronously.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.
        """
        pass

    @abstractmethod
    def send_sync(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a notification synchronously.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.
        """
        pass

    @abstractmethod
    async def test(self) -> bool:
        """
        Test if this backend is working.

        Returns:
            bool: True if test notification sent successfully.
        """
        pass


class Notifier:
    """
    Main notification dispatcher for DMLClean.

    The Notifier provides a unified API for sending notifications,
    with automatic backend selection and graceful degradation.

    Backend Selection Order:
    1. DesktopNotifierBackend (desktop-notifier library)
    2. PlyerBackend (plyer library)
    3. DummyBackend (no-op, always available)

    Attributes:
        config: Notifications configuration.
        backend: Currently selected backend.

    Example:
        ```python
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig()
        notifier = Notifier(config)

        # Send notification
        await notifier.send("Cleaning Complete", "Deleted 150 files")

        # Or use sync method
        notifier.send_sync("Error", "Something went wrong")
        ```
    """

    def __init__(self, config: NotificationsConfig | None = None) -> None:
        """
        Initialize the notifier with configuration.

        Args:
            config: Notifications configuration (created with defaults if None).
        """
        from dmlclean.config.schema import NotificationsConfig

        self.config = config or NotificationsConfig()
        self._backend: NotificationBackend | None = None
        self._initialized = False

        logger.debug("Notifier initialized")

    def _select_backend(self) -> NotificationBackend:
        """
        Select the best available notification backend.

        Tries backends in priority order:
        1. DesktopNotifierBackend (best features)
        2. PlyerBackend (good fallback)
        3. DummyBackend (no-op, always works)

        Returns:
            NotificationBackend: Best available backend.
        """
        from dmlclean.notifications.backends.desktop import DesktopNotifierBackend
        from dmlclean.notifications.backends.dummy import DummyBackend
        from dmlclean.notifications.backends.plyer_backend import PlyerBackend

        # Try desktop-notifier first (best features)
        desktop = DesktopNotifierBackend()
        if desktop.available:
            logger.info("Selected DesktopNotifierBackend for notifications")
            return desktop

        # Try plyer (good fallback)
        plyer = PlyerBackend()
        if plyer.available:
            logger.info("Selected PlyerBackend for notifications")
            return plyer

        # Fall back to dummy (no-op)
        logger.info("Selected DummyBackend for notifications (notifications disabled)")
        return DummyBackend()

    def _initialize(self) -> None:
        """
        Initialize the notifier (lazy initialization).

        Selects and initializes the best available backend.
        """
        if not self._initialized:
            self._backend = self._select_backend()
            self._initialized = True
            logger.debug(f"Notifier initialized with backend: {self._backend}")

    @property
    def backend(self) -> NotificationBackend:
        """
        Get the current notification backend.

        Returns:
            NotificationBackend: Current backend instance.
        """
        if not self._initialized:
            self._initialize()
        assert self._backend is not None, "Backend not initialized"
        return self._backend

    async def send(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a notification asynchronously.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.

        Example:
            ```python
            await notifier.send(
                "✓ Cleaning Complete",
                "Deleted 150 files (500 MB freed)"
            )
            ```
        """
        if not self.config.enabled:
            logger.debug("Notifications disabled, skipping")
            return False

        self._initialize()

        try:
            result = await self._backend.send(title, message, timeout)

            if result:
                logger.debug(f"Notification sent: {title}")
            else:
                logger.warning(f"Notification failed: {title}")

            return result

        except Exception as e:
            logger.error(f"Notification error: {e}")
            return False

    def send_sync(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a notification synchronously.

        Args:
            title: Notification title.
            message: Notification message body.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.

        Example:
            ```python
            notifier.send_sync(
                "Error",
                "Cleaning operation failed"
            )
            ```
        """
        if not self.config.enabled:
            logger.debug("Notifications disabled, skipping")
            return False

        self._initialize()

        try:
            result = self._backend.send_sync(title, message, timeout)

            if result:
                logger.debug(f"Sync notification sent: {title}")
            else:
                logger.warning(f"Sync notification failed: {title}")

            return result

        except Exception as e:
            logger.error(f"Sync notification error: {e}")
            return False

    async def send_clean_complete(
        self,
        files_deleted: int,
        size_bytes: int,
        mode: str,
    ) -> bool:
        """
        Send a "cleaning complete" notification.

        Args:
            files_deleted: Number of files deleted.
            size_bytes: Total size freed in bytes.
            mode: Clean mode used.

        Returns:
            bool: True if notification sent successfully.
        """
        from dmlclean.utils.sizes import humanize_size

        if not self.config.on_clean_complete:
            logger.debug("Clean complete notifications disabled")
            return False

        title = "✓ Cleaning Complete"
        message = f"Deleted {files_deleted:,} files ({humanize_size(size_bytes)} freed)"

        return await self.send(title, message, timeout=5)

    async def send_scan_complete(
        self,
        files_found: int,
        size_bytes: int,
    ) -> bool:
        """
        Send a "scan complete" notification.

        Args:
            files_found: Number of files found.
            size_bytes: Total size that can be freed.

        Returns:
            bool: True if notification sent successfully.
        """
        from dmlclean.utils.sizes import humanize_size

        if not self.config.on_scan_complete:
            logger.debug("Scan complete notifications disabled")
            return False

        title = "✓ Scan Complete"
        message = f"Found {files_found:,} cleanable files ({humanize_size(size_bytes)})"

        return await self.send(title, message, timeout=5)

    async def send_error(
        self,
        error_message: str,
    ) -> bool:
        """
        Send an error notification.

        Args:
            error_message: Error message to display.

        Returns:
            bool: True if notification sent successfully.
        """
        if not self.config.on_error:
            logger.debug("Error notifications disabled")
            return False

        title = "✗ DMLClean Error"
        message = error_message[:200]  # Truncate long messages

        return await self.send(title, message, timeout=10)

    async def send_protected_zone_violation(
        self,
        path: str,
        reason: str,
    ) -> bool:
        """
        Send a protected zone violation notification.

        Args:
            path: Path that was protected.
            reason: Reason for protection.

        Returns:
            bool: True if notification sent successfully.
        """
        if not self.config.on_protected_zone_violation:
            logger.debug("Protected zone notifications disabled")
            return False

        title = "⛔ Protected File"
        message = f"Blocked deletion: {path}\n{reason}"

        return await self.send(title, message, timeout=10)

    async def test(self) -> bool:
        """
        Test if notifications are working.

        Returns:
            bool: True if test notification sent successfully.
        """
        self._initialize()

        try:
            result = await self._backend.test()

            if result:
                logger.info("Notification test successful")
            else:
                logger.warning("Notification test failed")

            return result

        except Exception as e:
            logger.error(f"Notification test error: {e}")
            return False

    def get_backend_name(self) -> str:
        """
        Get the name of the current backend.

        Returns:
            str: Backend class name.
        """
        if not self._initialized:
            self._initialize()
        return self._backend.__class__.__name__


__all__ = ["NotificationBackend", "Notifier"]
