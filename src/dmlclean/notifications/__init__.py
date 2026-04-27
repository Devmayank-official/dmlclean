# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Notifications package for DMLClean.

This module provides desktop notification capabilities:
- Multi-platform desktop notifications
- Layered backend (desktop-notifier → plyer → dummy)
- Event-driven notification system
- Configurable per notification type

Example:
    ```python
    from dmlclean.notifications import Notifier, NotificationManager

    # Create notifier
    notifier = Notifier(config)

    # Send notification
    await notifier.send("Cleaning Complete", "Deleted 150 files")

    # Or use event-driven approach
    manager = NotificationManager()
    manager.subscribe_to_events()
    ```
"""

from dmlclean.notifications.backends.desktop import DesktopNotifierBackend
from dmlclean.notifications.backends.dummy import DummyBackend
from dmlclean.notifications.backends.plyer_backend import PlyerBackend
from dmlclean.notifications.manager import NotificationManager
from dmlclean.notifications.notifier import NotificationBackend, Notifier

__all__ = [
    "DesktopNotifierBackend",
    "DummyBackend",
    "NotificationBackend",
    "NotificationManager",
    "Notifier",
    "PlyerBackend",
]
