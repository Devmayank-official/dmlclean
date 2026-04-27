# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Notification manager for event-driven notifications.

Provides:
- Event subscription system
- Automatic notification dispatch
- Configurable per event type
- Decoupled architecture
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from dmlclean.domain.events import (
    CleanOperationCompleted,
    CleanOperationFailed,
    EventBus,
    ProtectedPathAdded,
    ProtectedPathRemoved,
    ScheduleCreated,
    UndoPerformed,
)

if TYPE_CHECKING:
    from dmlclean.config.schema import NotificationsConfig
    from dmlclean.notifications.notifier import Notifier


class NotificationManager:
    """
    Event-driven notification manager.

    The NotificationManager subscribes to domain events
    and automatically sends appropriate notifications.

    This provides decoupled architecture where:
    - Services publish events
    - Manager listens and sends notifications
    - No direct coupling between services and notifications

    Attributes:
        notifier: Notification dispatcher instance.
        config: Notifications configuration.

    Example:
        ```python
        from dmlclean.container import get_container

        container = get_container()
        manager = NotificationManager(container.config.schema.notifications)

        # Subscribe to all events
        manager.subscribe_to_events()

        # Now notifications are sent automatically
        # when events are published
        ```
    """

    def __init__(
        self,
        config: NotificationsConfig | None = None,
        notifier: Notifier | None = None,
    ) -> None:
        """
        Initialize the notification manager.

        Args:
            config: Notifications configuration.
            notifier: Notifier instance (created if None).
        """
        from dmlclean.config.schema import NotificationsConfig
        from dmlclean.notifications.notifier import Notifier

        self.config = config or NotificationsConfig()
        self.notifier = notifier or Notifier(self.config)

        self._subscribed = False
        logger.debug("NotificationManager initialized")

    def subscribe_to_events(self) -> None:
        """
        Subscribe to all domain events.

        This method registers event handlers for:
        - CleanOperationCompleted
        - CleanOperationFailed
        - ProtectedPathAdded
        - ProtectedPathRemoved
        - ScheduleCreated
        - UndoPerformed

        Example:
            ```python
            manager.subscribe_to_events()
            # Now events automatically trigger notifications
            ```
        """
        if self._subscribed:
            logger.debug("NotificationManager already subscribed to events")
            return

        # Subscribe to clean operation events
        EventBus.subscribe(CleanOperationCompleted, self._handle_clean_completed)
        EventBus.subscribe(CleanOperationFailed, self._handle_clean_failed)

        # Subscribe to protection events
        EventBus.subscribe(ProtectedPathAdded, self._handle_protected_path_added)
        EventBus.subscribe(ProtectedPathRemoved, self._handle_protected_path_removed)

        # Subscribe to schedule events
        EventBus.subscribe(ScheduleCreated, self._handle_schedule_created)

        # Subscribe to undo events
        EventBus.subscribe(UndoPerformed, self._handle_undo_performed)

        self._subscribed = True
        logger.info("NotificationManager subscribed to all domain events")

    def unsubscribe_from_events(self) -> None:
        """
        Unsubscribe from all domain events.

        This removes all event handlers registered by this manager.
        """
        if not self._subscribed:
            logger.debug("NotificationManager not subscribed to events")
            return

        # Unsubscribe from all events
        EventBus.clear()

        self._subscribed = False
        logger.info("NotificationManager unsubscribed from all events")

    async def _handle_clean_completed(self, event: CleanOperationCompleted) -> None:
        """
        Handle clean operation completed event.

        Args:
            event: Clean operation completed event.
        """
        if not self.config.on_clean_complete:
            logger.debug("Clean complete notifications disabled")
            return

        try:
            await self.notifier.send_clean_complete(
                files_deleted=event.files_deleted,
                size_bytes=event.size_bytes,
                mode=event.mode,
            )
        except Exception as e:
            logger.error(f"Error sending clean complete notification: {e}")

    async def _handle_clean_failed(self, event: CleanOperationFailed) -> None:
        """
        Handle clean operation failed event.

        Args:
            event: Clean operation failed event.
        """
        if not self.config.on_error:
            logger.debug("Error notifications disabled")
            return

        try:
            await self.notifier.send_error(
                error_message=f"{event.error_type}: {event.error_message}",
            )
        except Exception as e:
            logger.error(f"Error sending clean failed notification: {e}")

    async def _handle_protected_path_added(
        self,
        event: ProtectedPathAdded,
    ) -> None:
        """
        Handle protected path added event.

        Args:
            event: Protected path added event.
        """
        try:
            # Send info notification (optional, can be disabled)
            await self.notifier.send(
                title="✓ Path Protected",
                message=f"Added to protected zone: {event.path}",
                timeout=3,
            )
        except Exception as e:
            logger.error(f"Error sending protected path added notification: {e}")

    async def _handle_protected_path_removed(
        self,
        event: ProtectedPathRemoved,
    ) -> None:
        """
        Handle protected path removed event.

        Args:
            event: Protected path removed event.
        """
        try:
            await self.notifier.send(
                title="ℹ Protection Removed",
                message=f"Removed from protected zone: {event.path}",
                timeout=3,
            )
        except Exception as e:
            logger.error(f"Error sending protected path removed notification: {e}")

    async def _handle_schedule_created(self, event: ScheduleCreated) -> None:
        """
        Handle schedule created event.

        Args:
            event: Schedule created event.
        """
        try:
            await self.notifier.send(
                title="✓ Schedule Created",
                message=f"{event.name} ({event.cron_expression})",
                timeout=3,
            )
        except Exception as e:
            logger.error(f"Error sending schedule created notification: {e}")

    async def _handle_undo_performed(self, event: UndoPerformed) -> None:
        """
        Handle undo performed event.

        Args:
            event: Undo performed event.
        """
        try:
            if event.dry_run:
                title = "ℹ Undo Preview"
                message = f"Would restore {event.files_restored} files"
            else:
                title = "✓ Undo Complete"
                message = f"Restored {event.files_restored} files"

            await self.notifier.send(title=title, message=message, timeout=3)

        except Exception as e:
            logger.error(f"Error sending undo performed notification: {e}")

    def send_custom_notification(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a custom notification synchronously.

        Args:
            title: Notification title.
            message: Notification message.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.

        Example:
            ```python
            manager.send_custom_notification(
                "Custom Alert",
                "Something happened!"
            )
            ```
        """
        return self.notifier.send_sync(title, message, timeout)

    async def send_custom_notification_async(
        self,
        title: str,
        message: str,
        timeout: int = 5,
    ) -> bool:
        """
        Send a custom notification asynchronously.

        Args:
            title: Notification title.
            message: Notification message.
            timeout: Notification timeout in seconds.

        Returns:
            bool: True if notification sent successfully.
        """
        return await self.notifier.send(title, message, timeout)

    def test_notifications(self) -> bool:
        """
        Test if notifications are working.

        Returns:
            bool: True if test notification sent successfully.
        """
        return self.notifier.send_sync(
            "DMLClean Test",
            "Notifications are working correctly!",
            timeout=3,
        )

    def get_status(self) -> dict[str, Any]:
        """
        Get notification manager status.

        Returns:
            dict: Status information including:
                - enabled: Whether notifications are enabled
                - backend: Current backend name
                - subscribed: Whether subscribed to events
                - config: Notification settings

        Example:
            ```python
            status = manager.get_status()
            print(f"Backend: {status['backend']}")
            print(f"Subscribed: {status['subscribed']}")
            ```
        """
        return {
            "enabled": self.config.enabled,
            "backend": self.notifier.get_backend_name(),
            "subscribed": self._subscribed,
            "config": {
                "on_clean_complete": self.config.on_clean_complete,
                "on_scan_complete": self.config.on_scan_complete,
                "on_error": self.config.on_error,
                "on_scheduled_run": self.config.on_scheduled_run,
                "on_protected_zone_violation": self.config.on_protected_zone_violation,
            },
        }


__all__ = ["NotificationManager"]
