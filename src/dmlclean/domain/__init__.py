# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Domain Layer for DMLClean.

The domain layer contains pure business logic and domain models.
It has no dependencies on infrastructure (database, filesystem, etc.)
making it highly testable and reusable.

This layer includes:
- Domain Events (events.py): Business occurrences
- Domain Entities: Business objects with identity
- Value Objects: Immutable domain concepts
- Domain Services: Pure business logic

Architecture:
    ```
    Domain Layer (this package)
        ↓ (depends on)
    Nothing! (Pure business logic)

    Other layers depend on Domain, not vice versa.
    ```
"""

from dmlclean.domain.events import (
    CleanOperationCompleted,
    CleanOperationFailed,
    DomainEvent,
    EventBus,
    ProtectedPathAdded,
    ProtectedPathRemoved,
    ScheduleCreated,
    ScheduleExecuted,
    UndoPerformed,
    event_handler,
)

__all__ = [
    "CleanOperationCompleted",
    "CleanOperationFailed",
    # Events
    "DomainEvent",
    # Event Bus
    "EventBus",
    "ProtectedPathAdded",
    "ProtectedPathRemoved",
    "ScheduleCreated",
    "ScheduleExecuted",
    "UndoPerformed",
    "event_handler",
]
