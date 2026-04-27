# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Domain Events for DMLClean.

Domain events capture something meaningful that happens in the domain.
They are used to:
- Decouple business logic from side effects
- Enable event-driven architecture
- Support auditing and compliance
- Trigger notifications and metrics

Events in DMLClean:
- CleanOperationCompleted: Cleaning operation finished
- CleanOperationFailed: Cleaning operation failed
- ProtectedPathAdded: Path added to protected zone
- ProtectedPathRemoved: Path removed from protected zone
- ScheduleCreated: Cleaning schedule created
- ScheduleExecuted: Scheduled cleaning ran
- UndoPerformed: Files restored from trash

Example:
    ```python
    from dmlclean.domain.events import (
        CleanOperationCompleted,
        EventBus,
        event_handler,
    )

    # Define event handler
    @event_handler(CleanOperationCompleted)
    def log_clean_metrics(event: CleanOperationCompleted) -> None:
        logger.info(f"Cleaned {event.files_deleted} files")

    # Publish event
    EventBus.publish(CleanOperationCompleted(
        operation_id="abc123",
        files_deleted=150,
        size_bytes=1024*1024*50,
    ))
    ```
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar

from loguru import logger

# ============================================================================
# DOMAIN EVENTS
# ============================================================================


@dataclass
class DomainEvent:
    """
    Base class for all domain events.

    All domain events should inherit from this base class.
    Events are immutable dataclasses containing all relevant information
    about the domain occurrence.

    Attributes:
        timestamp: When the event occurred (ISO 8601 format).
        event_type: Event class name (auto-populated).
    """

    timestamp: str = field(init=False)
    event_type: str = field(init=False)

    def __post_init__(self) -> None:
        """Auto-populate timestamp and event_type."""
        if not hasattr(self, "timestamp"):
            object.__setattr__(self, "timestamp", datetime.now(UTC).isoformat())
        if not hasattr(self, "event_type"):
            object.__setattr__(self, "event_type", self.__class__.__name__)


@dataclass
class ScanCompleted(DomainEvent):
    """
    Event emitted when a scan operation completes successfully.

    This event is published after files have been scanned and analyzed.

    Attributes:
        operation_id: Unique operation identifier (UUID).
        mode: Scan mode used (fast, deep, custom).
        paths_scanned: Number of paths scanned.
        files_found: Number of files found during scan.
        size_bytes: Total size found in bytes.
        candidates: Number of cleanable candidates identified.
        duration_ms: Scan duration in milliseconds.
        categories: List of categories scanned.
    """

    operation_id: str
    mode: str
    paths_scanned: int
    files_found: int
    size_bytes: int
    candidates: int
    duration_ms: int
    categories: list[str] | None = None


@dataclass
class CleanOperationCompleted(DomainEvent):
    """
    Event emitted when a cleaning operation completes successfully.

    This event is published after files have been cleaned and the
    operation has been recorded in history.

    Attributes:
        operation_id: Unique operation identifier (UUID).
        mode: Clean mode used (dry-run, trash, permanent).
        profile: Cleaning profile used.
        scan_mode: Scan mode used (fast, deep, custom).
        files_found: Number of files found during scan.
        files_deleted: Number of files actually deleted.
        size_bytes: Total size freed in bytes.
        duration_ms: Operation duration in milliseconds.
        categories: List of categories cleaned.
        paths_cleaned: Number of paths cleaned.
    """

    operation_id: str
    mode: str
    profile: str
    scan_mode: str
    files_found: int
    files_deleted: int
    size_bytes: int
    duration_ms: int
    categories: list[str] | None = None
    paths_cleaned: int = 1


@dataclass
class CleanOperationFailed(DomainEvent):
    """
    Event emitted when a cleaning operation fails.

    This event is published when an exception occurs during cleaning.

    Attributes:
        operation_id: Unique operation identifier (UUID).
        mode: Clean mode being used.
        profile: Cleaning profile being used.
        error_message: Human-readable error description.
        error_type: Exception class name.
        paths_attempted: Number of paths being cleaned.
    """

    operation_id: str
    mode: str
    profile: str
    error_message: str
    error_type: str
    paths_attempted: int = 1


@dataclass
class ProtectedPathAdded(DomainEvent):
    """
    Event emitted when a path is added to the Protected Zone.

    This event is published after a new protection rule is created.

    Attributes:
        entry_id: Unique entry identifier (UUID).
        path: Protected path or glob pattern.
        description: Human-readable description.
        is_glob: Whether the path is a glob pattern.
    """

    entry_id: str
    path: str
    description: str
    is_glob: bool


@dataclass
class ProtectedPathRemoved(DomainEvent):
    """
    Event emitted when a path is removed from the Protected Zone.

    This event is published after a protection rule is deleted.

    Attributes:
        entry_id: Unique entry identifier (UUID).
        path: Protected path that was removed.
    """

    entry_id: str
    path: str


@dataclass
class ScheduleCreated(DomainEvent):
    """
    Event emitted when a cleaning schedule is created.

    This event is published after a new scheduled job is created.

    Attributes:
        job_id: Unique job identifier (UUID).
        name: Human-readable job name.
        cron_expression: Cron expression for scheduling.
        profile: Cleaning profile to use.
        clean_mode: Clean mode to use.
        enabled: Whether the schedule is active.
    """

    job_id: str
    name: str
    cron_expression: str
    profile: str
    clean_mode: str
    enabled: bool = True


@dataclass
class ScheduleExecuted(DomainEvent):
    """
    Event emitted when a scheduled cleaning runs.

    This event is published after a scheduled job executes.

    Attributes:
        job_id: Unique job identifier (UUID).
        job_name: Human-readable job name.
        success: Whether execution succeeded.
        files_deleted: Number of files deleted (if successful).
        size_bytes: Total size freed (if successful).
        error_message: Error message (if failed).
        duration_ms: Execution duration in milliseconds.
    """

    job_id: str
    job_name: str
    success: bool
    files_deleted: int = 0
    size_bytes: int = 0
    error_message: str | None = None
    duration_ms: int = 0


@dataclass
class UndoPerformed(DomainEvent):
    """
    Event emitted when files are restored from trash.

    This event is published after an undo operation completes.

    Attributes:
        operation_id: Original operation identifier being undone.
        files_restored: Number of files successfully restored.
        files_failed: Number of files that failed to restore.
        dry_run: Whether this was a simulation only.
    """

    operation_id: str
    files_restored: int
    files_failed: int
    dry_run: bool = False


# ============================================================================
# EVENT BUS
# ============================================================================


class EventBus:
    """
    Simple in-memory event bus for domain events.

    The EventBus provides publish-subscribe functionality for domain events.
    Handlers can subscribe to specific event types and will be notified
    when those events are published.

    This implementation is synchronous and in-memory. For production use
    with persistence, consider integrating with a message queue.

    Example:
        ```python
        from dmlclean.domain.events import EventBus, CleanOperationCompleted

        # Subscribe to event
        @event_handler(CleanOperationCompleted)
        def log_clean(event: CleanOperationCompleted) -> None:
            logger.info(f"Cleaned {event.files_deleted} files")

        # Publish event
        EventBus.publish(CleanOperationCompleted(
            operation_id="abc123",
            files_deleted=150,
            ...
        ))
        ```
    """

    # Class-level handler registry
    _handlers: ClassVar[dict[type[DomainEvent], list[Callable[[DomainEvent], None]]]] = {}

    @classmethod
    def subscribe(
        cls, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Event class to subscribe to.
            handler: Function to call when event is published.

        Example:
            ```python
            def my_handler(event: CleanOperationCompleted) -> None:
                logger.info(f"Event: {event.operation_id}")

            EventBus.subscribe(CleanOperationCompleted, my_handler)
            ```
        """
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
        logger.debug(f"EventBus: Subscribed handler to {event_type.__name__}")

    @classmethod
    def unsubscribe(
        cls, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: Event class to unsubscribe from.
            handler: Handler function to remove.

        Returns:
            bool: True if handler was removed.

        Example:
            ```python
            removed = EventBus.unsubscribe(CleanOperationCompleted, my_handler)
            ```
        """
        if event_type in cls._handlers:
            try:
                cls._handlers[event_type].remove(handler)
                logger.debug(f"EventBus: Unsubscribed handler from {event_type.__name__}")
                return True
            except ValueError:
                pass
        return False

    @classmethod
    def publish(cls, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed handlers.

        This method calls all handlers subscribed to the event's type.
        Supports both sync and async handlers.
        Exceptions in handlers are logged but don't stop other handlers.

        Args:
            event: Event instance to publish.

        Example:
            ```python
            event = CleanOperationCompleted(
                operation_id="abc123",
                files_deleted=150,
                ...
            )
            EventBus.publish(event)
            ```
        """
        import asyncio
        import inspect

        event_type = type(event)
        handlers = cls._handlers.get(event_type, [])

        # Also check parent classes (for inheritance)
        for base_class in event_type.__mro__:
            if base_class in cls._handlers and base_class is not event_type:
                handlers.extend(cls._handlers[base_class])

        if not handlers:
            logger.debug(f"EventBus: No handlers for {event_type.__name__}")
            return

        logger.debug(f"EventBus: Publishing {event_type.__name__} to {len(handlers)} handler(s)")

        for handler in handlers:
            try:
                # Check if handler is async
                if inspect.iscoroutinefunction(handler):
                    # Try to run async handler
                    try:
                        asyncio.get_running_loop()
                        # We're in a running loop, create a task
                        asyncio.create_task(handler(event))
                    except RuntimeError:
                        # No running loop, run it
                        asyncio.run(handler(event))
                else:
                    # Sync handler
                    handler(event)
            except Exception as e:
                logger.error(
                    f"EventBus: Handler failed for {event_type.__name__}: {e}", exc_info=True
                )

    @classmethod
    def clear(cls) -> None:
        """
        Clear all event handlers.

        This is primarily useful for testing.

        Example:
            ```python
            # Clear handlers between tests
            EventBus.clear()
            ```
        """
        cls._handlers.clear()
        logger.debug("EventBus: All handlers cleared")

    @classmethod
    def get_handler_count(cls, event_type: type[DomainEvent] | None = None) -> int:
        """
        Get number of registered handlers.

        Args:
            event_type: Specific event type (None = all types).

        Returns:
            int: Number of handlers.

        Example:
            ```python
            total = EventBus.get_handler_count()
            clean_handlers = EventBus.get_handler_count(CleanOperationCompleted)
            ```
        """
        if event_type:
            return len(cls._handlers.get(event_type, []))
        return sum(len(handlers) for handlers in cls._handlers.values())


# ============================================================================
# DECORATOR
# ============================================================================


def event_handler(
    event_type: type[DomainEvent],
) -> Callable[[Callable[[Any], None]], Callable[[Any], None]]:
    """
    Decorator for registering event handlers.

    This decorator provides a clean syntax for subscribing handlers
    to events.

    Usage:
        ```python
        @event_handler(CleanOperationCompleted)
        def log_clean(event: CleanOperationCompleted) -> None:
            logger.info(f"Cleaned {event.files_deleted} files")

        @event_handler(ProtectedPathAdded)
        def notify_protection(event: ProtectedPathAdded) -> None:
            send_notification(f"Protected: {event.path}")
        ```

    Args:
        event_type: Event class to handle.

    Returns:
        Decorator function.
    """

    def decorator(handler: Callable[[Any], None]) -> Callable[[Any], None]:
        EventBus.subscribe(event_type, handler)
        logger.debug(f"Registered event handler for {event_type.__name__}")
        return handler

    return decorator


# ============================================================================
# BUILT-IN HANDLERS
# ============================================================================


@event_handler(CleanOperationCompleted)
def _log_clean_completion(event: CleanOperationCompleted) -> None:
    """Log clean operation completion."""
    from dmlclean.utils.sizes import humanize_size

    logger.info(
        f"✓ Clean completed: {event.files_deleted} files, "
        f"{humanize_size(event.size_bytes)} freed, "
        f"{event.duration_ms}ms"
    )


@event_handler(CleanOperationFailed)
def _log_clean_failure(event: CleanOperationFailed) -> None:
    """Log clean operation failure."""
    logger.error(
        f"✗ Clean failed: {event.error_type} - {event.error_message} "
        f"(Operation: {event.operation_id})"
    )


@event_handler(ProtectedPathAdded)
def _log_protection_added(event: ProtectedPathAdded) -> None:
    """Log when path is protected."""
    path_type = "Glob" if event.is_glob else "Path"
    logger.info(f"✓ Protected {path_type} added: {event.path}")


@event_handler(ScheduleCreated)
def _log_schedule_created(event: ScheduleCreated) -> None:
    """Log when schedule is created."""
    logger.info(f"✓ Schedule created: {event.name} ({event.cron_expression})")


__all__ = [
    # Events
    "CleanOperationCompleted",
    "CleanOperationFailed",
    # Base
    "DomainEvent",
    # Event Bus
    "EventBus",
    "ProtectedPathAdded",
    "ProtectedPathRemoved",
    "ScheduleCreated",
    "ScheduleExecuted",
    "UndoPerformed",
    # Decorator
    "event_handler",
]
