# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Notification backends for DMLClean.

Provides multiple notification backend implementations:
- Desktop notifier (primary, feature-rich)
- Plyer (fallback, cross-platform)
- Dummy (no-op, for testing/disabled)
"""

from dmlclean.notifications.backends.desktop import DesktopNotifierBackend
from dmlclean.notifications.backends.dummy import DummyBackend
from dmlclean.notifications.backends.plyer_backend import PlyerBackend

__all__ = [
    "DesktopNotifierBackend",
    "DummyBackend",
    "PlyerBackend",
]
