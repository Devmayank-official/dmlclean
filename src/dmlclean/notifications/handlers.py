# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Event-Driven Notification Handlers for DMLClean.

Uses direct desktop_notifier API - simple and reliable!
"""

from __future__ import annotations

import asyncio

from loguru import logger

from dmlclean.domain.events import (
    CleanOperationCompleted,
    CleanOperationFailed,
    ProtectedPathAdded,
    ScanCompleted,
    ScheduleCreated,
    event_handler,
)
from dmlclean.utils.sizes import humanize_size


def _send_notification(title: str, message: str) -> bool:
    """Send desktop notification using desktop_notifier.DesktopNotifier."""
    try:
        import desktop_notifier

        notifier = desktop_notifier.DesktopNotifier()

        # Fire-and-forget async
        try:
            asyncio.get_running_loop()
            asyncio.create_task(notifier.send(title, message))
        except RuntimeError:
            asyncio.run(notifier.send(title, message))

        logger.info(f"✓ Notification sent: {title}")
        return True
    except Exception as e:
        logger.warning(f"Notification failed: {e}")
        return False


@event_handler(ScanCompleted)
def _notify_scan(event: ScanCompleted) -> None:
    """Notify on scan complete."""
    title = "✓ Scan Complete"
    message = f"Found {event.candidates:,} files\n{humanize_size(event.size_bytes)} can be freed"
    _send_notification(title, message)


@event_handler(CleanOperationCompleted)
def _notify_clean_complete(event: CleanOperationCompleted) -> None:
    """Notify on clean complete."""
    title = "✓ Cleaning Complete"
    message = f"Freed {humanize_size(event.size_bytes)}\n{event.files_deleted:,} files"
    _send_notification(title, message)


@event_handler(CleanOperationFailed)
def _notify_clean_failed(event: CleanOperationFailed) -> None:
    """Notify on clean failed."""
    title = "✗ Cleaning Failed"
    message = f"{event.error_type}: {event.error_message[:100]}"
    _send_notification(title, message)


@event_handler(ProtectedPathAdded)
def _notify_protect(event: ProtectedPathAdded) -> None:
    """Notify on path protected."""
    ptype = "Glob" if event.is_glob else "Path"
    title = "✓ Path Protected"
    message = f"{ptype}: {event.path[:80]}"
    _send_notification(title, message)


@event_handler(ScheduleCreated)
def _notify_schedule(event: ScheduleCreated) -> None:
    """Notify on schedule created."""
    title = "✓ Schedule Created"
    message = f"{event.name}\nCron: {event.cron_expression}"
    _send_notification(title, message)


__all__ = [
    "_notify_clean_complete",
    "_notify_clean_failed",
    "_notify_protect",
    "_notify_scan",
    "_notify_schedule",
]
