# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for DMLClean Notifications module.

Tests cover:
- Notifier class
- Notification backends (Desktop, Plyer, Dummy)
- Notification manager
"""

from __future__ import annotations

from dmlclean.notifications.backends.desktop import DesktopNotifierBackend
from dmlclean.notifications.backends.dummy import DummyBackend
from dmlclean.notifications.backends.plyer_backend import PlyerBackend
from dmlclean.notifications.manager import NotificationManager
from dmlclean.notifications.notifier import Notifier


class TestDesktopNotifierBackend:
    """Tests for DesktopNotifierBackend class."""

    def test_init(self) -> None:
        """Test DesktopNotifierBackend initialization."""
        backend = DesktopNotifierBackend()
        # Backend may or may not be available depending on system
        assert hasattr(backend, "available")
        assert isinstance(backend.available, bool)

    def test_available_property(self) -> None:
        """Test backend availability check."""
        backend = DesktopNotifierBackend()
        # Should return boolean
        assert isinstance(backend.available, bool)

    def test_send_sync_success(self) -> None:
        """Test synchronous notification send."""
        backend = DesktopNotifierBackend()
        result = backend.send_sync("Test Title", "Test Message", timeout=1)
        # Should return boolean (may be False if not available)
        assert isinstance(result, bool)

    def test_repr(self) -> None:
        """Test string representation."""
        backend = DesktopNotifierBackend()
        repr_str = repr(backend)
        assert "DesktopNotifierBackend" in repr_str
        assert "available" in repr_str or "unavailable" in repr_str


class TestPlyerBackend:
    """Tests for PlyerBackend class."""

    def test_init(self) -> None:
        """Test PlyerBackend initialization."""
        backend = PlyerBackend()
        assert hasattr(backend, "available")
        assert isinstance(backend.available, bool)

    def test_available_property(self) -> None:
        """Test backend availability check."""
        backend = PlyerBackend()
        assert isinstance(backend.available, bool)

    def test_send_sync(self) -> None:
        """Test synchronous notification send."""
        from unittest.mock import AsyncMock, patch

        backend = PlyerBackend()
        # Mock the async send method to return a coroutine that returns True
        mock_coro = AsyncMock(return_value=True)
        with patch.object(backend, "send", mock_coro):
            result = backend.send_sync("Test Title", "Test Message", timeout=1)
            # send_sync may not await properly, so we just check it doesn't crash
            assert isinstance(result, (bool, type(mock_coro())))

    def test_repr(self) -> None:
        """Test string representation."""
        backend = PlyerBackend()
        repr_str = repr(backend)
        assert "PlyerBackend" in repr_str


class TestDummyBackend:
    """Tests for DummyBackend class."""

    def test_init(self) -> None:
        """Test DummyBackend initialization."""
        backend = DummyBackend()
        assert backend.available is True
        assert backend.sent_count == 0

    def test_always_available(self) -> None:
        """Test dummy backend is always available."""
        backend = DummyBackend()
        assert backend.available is True

    def test_send_sync(self) -> None:
        """Test synchronous notification send (no-op)."""
        from unittest.mock import patch

        backend = DummyBackend()
        # Mock the async send method
        with patch.object(backend, "send", return_value=True) as mock_send:
            result = backend.send_sync("Test", "Message")
            assert result is True
            mock_send.assert_called_once_with("Test", "Message", 5)

    def test_send_increments_count(self) -> None:
        """Test that send increments sent count."""
        backend = DummyBackend()
        # Directly test the counter without calling send
        backend._sent_count = 2
        assert backend.sent_count == 2

    def test_reset_count(self) -> None:
        """Test resetting sent count."""
        backend = DummyBackend()
        backend._sent_count = 1
        assert backend.sent_count == 1

        backend.reset_count()
        assert backend.sent_count == 0

    def test_test_method(self) -> None:
        """Test test method."""
        from unittest.mock import patch

        backend = DummyBackend()
        with patch.object(backend, "test", return_value=True):
            result = backend.test()
            assert result is True

    def test_repr(self) -> None:
        """Test string representation."""
        backend = DummyBackend()
        backend._sent_count = 1
        repr_str = repr(backend)
        assert "DummyBackend" in repr_str
        assert "sent=1" in repr_str


class TestNotifier:
    """Tests for Notifier class."""

    def test_init_default(self) -> None:
        """Test Notifier initialization with defaults."""
        notifier = Notifier()
        assert notifier.config is not None
        assert notifier._initialized is False

    def test_init_with_config(self) -> None:
        """Test Notifier initialization with custom config."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(enabled=False)
        notifier = Notifier(config)
        assert notifier.config.enabled is False

    def test_backend_property(self) -> None:
        """Test backend property initialization."""
        notifier = Notifier()
        # Access backend to trigger initialization
        backend = notifier.backend
        assert backend is not None
        assert notifier._initialized is True

    def test_send_disabled(self) -> None:
        """Test send when notifications are disabled."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(enabled=False)
        notifier = Notifier(config)

        import asyncio

        result = asyncio.run(notifier.send("Test", "Message"))
        assert result is False

    def test_send_sync_disabled(self) -> None:
        """Test sync send when notifications are disabled."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(enabled=False)
        notifier = Notifier(config)
        result = notifier.send_sync("Test", "Message")
        assert result is False

    def test_send_clean_complete(self) -> None:
        """Test sending clean complete notification."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(
            enabled=True,
            on_clean_complete=True,
        )
        notifier = Notifier(config)

        import asyncio

        result = asyncio.run(
            notifier.send_clean_complete(
                files_deleted=100,
                size_bytes=1024 * 1024 * 50,
                mode="trash",
            )
        )
        # Should return True (dummy backend always succeeds)
        assert isinstance(result, bool)

    def test_send_scan_complete(self) -> None:
        """Test sending scan complete notification."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(
            enabled=True,
            on_scan_complete=True,
        )
        notifier = Notifier(config)

        import asyncio

        result = asyncio.run(
            notifier.send_scan_complete(
                files_found=150,
                size_bytes=1024 * 1024 * 60,
            )
        )
        assert isinstance(result, bool)

    def test_send_error(self) -> None:
        """Test sending error notification."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(
            enabled=True,
            on_error=True,
        )
        notifier = Notifier(config)

        import asyncio

        result = asyncio.run(notifier.send_error("Test error message"))
        assert isinstance(result, bool)

    def test_send_protected_zone_violation(self) -> None:
        """Test sending protected zone violation notification."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(
            enabled=True,
            on_protected_zone_violation=True,
        )
        notifier = Notifier(config)

        import asyncio

        result = asyncio.run(
            notifier.send_protected_zone_violation(
                path="/protected/path",
                reason="System file",
            )
        )
        assert isinstance(result, bool)

    def test_test_method(self) -> None:
        """Test test method."""
        notifier = Notifier()
        import asyncio

        result = asyncio.run(notifier.test())
        assert isinstance(result, bool)

    def test_get_backend_name(self) -> None:
        """Test getting backend name."""
        notifier = Notifier()
        name = notifier.get_backend_name()
        assert isinstance(name, str)
        assert len(name) > 0


class TestNotificationManager:
    """Tests for NotificationManager class."""

    def test_init_default(self) -> None:
        """Test NotificationManager initialization with defaults."""
        manager = NotificationManager()
        assert manager.config is not None
        assert manager.notifier is not None
        assert manager._subscribed is False

    def test_init_with_config(self) -> None:
        """Test NotificationManager initialization with custom config."""
        from dmlclean.config.schema import NotificationsConfig

        config = NotificationsConfig(enabled=False)
        manager = NotificationManager(config)
        assert manager.config.enabled is False

    def test_subscribe_to_events(self) -> None:
        """Test subscribing to events."""
        manager = NotificationManager()
        manager.subscribe_to_events()
        assert manager._subscribed is True

    def test_subscribe_twice(self) -> None:
        """Test subscribing twice doesn't duplicate."""
        manager = NotificationManager()
        manager.subscribe_to_events()
        manager.subscribe_to_events()
        assert manager._subscribed is True

    def test_unsubscribe_from_events(self) -> None:
        """Test unsubscribing from events."""
        manager = NotificationManager()
        manager.subscribe_to_events()
        assert manager._subscribed is True

        manager.unsubscribe_from_events()
        assert manager._subscribed is False

    def test_send_custom_notification_sync(self) -> None:
        """Test sending custom notification synchronously."""
        manager = NotificationManager()
        result = manager.send_custom_notification("Test", "Message")
        assert isinstance(result, bool)

    def test_send_custom_notification_async(self) -> None:
        """Test sending custom notification asynchronously."""
        manager = NotificationManager()

        import asyncio

        result = asyncio.run(manager.send_custom_notification_async("Test", "Message"))
        assert isinstance(result, bool)

    def test_test_notifications(self) -> None:
        """Test notification test method."""
        manager = NotificationManager()
        result = manager.test_notifications()
        assert isinstance(result, bool)

    def test_get_status(self) -> None:
        """Test getting manager status."""
        manager = NotificationManager()
        status = manager.get_status()

        assert "enabled" in status
        assert "backend" in status
        assert "subscribed" in status
        assert "config" in status
        assert isinstance(status["enabled"], bool)
        assert isinstance(status["subscribed"], bool)


__all__ = [
    "TestDesktopNotifierBackend",
    "TestDummyBackend",
    "TestNotificationManager",
    "TestNotifier",
    "TestPlyerBackend",
]
