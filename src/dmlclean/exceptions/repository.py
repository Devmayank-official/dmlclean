# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Repository exception hierarchy for DMLClean.

This module provides custom exceptions for repository operations,
enabling consistent error handling across all data access layers.

Example:
    ```python
    from dmlclean.exceptions.repository import (
        RepositoryError,
        NotFoundError,
        DuplicateError,
        IntegrityError,
    )

    try:
        entry = history_repo.get_or_raise("invalid-id")
    except NotFoundError as e:
        logger.error(f"Entry not found: {e}")

    try:
        repo.create(entity)
    except DuplicateError as e:
        logger.error(f"Duplicate entry: {e}")
    ```
"""

from __future__ import annotations

from dmlclean.exceptions.base import DMLCleanError


class RepositoryError(DMLCleanError):
    """
    Base exception for repository operations.

    All repository-related exceptions inherit from this class.
    Use this for catching any repository error.

    Attributes:
        message: Human-readable error message.
        exit_code: Process exit code (default: 1).
        entity_type: Optional entity type name for context.
        entity_id: Optional entity ID for context.

    Example:
        ```python
        try:
            repo.create(entity)
        except RepositoryError as e:
            logger.error(f"Repository error: {e.message}")
            raise
        ```
    """

    def __init__(
        self,
        message: str,
        exit_code: int = 1,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> None:
        """
        Initialize a RepositoryError.

        Args:
            message: Human-readable error message.
            exit_code: Process exit code (default: 1).
            entity_type: Optional entity type name for context.
            entity_id: Optional entity ID for context.
        """
        super().__init__(message, exit_code)
        self.entity_type = entity_type
        self.entity_id = entity_id

    def __str__(self) -> str:
        """Return the error message with context if available."""
        if self.entity_type and self.entity_id:
            return f"{self.message} ({self.entity_type}[{self.entity_id}])"
        return self.message

    def __repr__(self) -> str:
        """Return a repr string for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"exit_code={self.exit_code}, "
            f"entity_type={self.entity_type!r}, "
            f"entity_id={self.entity_id!r}"
            ")"
        )


class NotFoundError(RepositoryError):
    """
    Exception raised when an entity is not found.

    This is raised by `get_or_raise()` and other methods that
    expect an entity to exist.

    Attributes:
        message: Human-readable error message.
        entity_type: The type of entity that was not found.
        entity_id: The ID that was searched for.

    Example:
        ```python
        def get_by_id(self, id: str) -> HistoryEntry | None:
            row = self.db.fetchone("SELECT * FROM history WHERE id = ?", (id,))
            if row is None:
                raise NotFoundError(
                    f"History entry not found",
                    entity_type="HistoryEntry",
                    entity_id=id,
                )
            return HistoryEntry.from_row(row)
        ```
    """

    def __init__(
        self,
        message: str = "Entity not found",
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> None:
        """
        Initialize a NotFoundError.

        Args:
            message: Human-readable error message.
            entity_type: The type of entity that was not found.
            entity_id: The ID that was searched for.
        """
        super().__init__(
            message,
            exit_code=1,
            entity_type=entity_type,
            entity_id=entity_id,
        )


class DuplicateError(RepositoryError):
    """
    Exception raised when creating a duplicate entity.

    This is raised when attempting to create an entity with
    an ID or unique key that already exists.

    Attributes:
        message: Human-readable error message.
        entity_type: The type of entity that is duplicated.
        entity_id: The conflicting ID or key.

    Example:
        ```python
        def create(self, entry: HistoryEntry) -> str:
            if self.exists(entry.id):
                raise DuplicateError(
                    f"History entry already exists",
                    entity_type="HistoryEntry",
                    entity_id=entry.id,
                )
            # ... create logic
            return entry.id
        ```
    """

    def __init__(
        self,
        message: str = "Duplicate entity",
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> None:
        """
        Initialize a DuplicateError.

        Args:
            message: Human-readable error message.
            entity_type: The type of entity that is duplicated.
            entity_id: The conflicting ID or key.
        """
        super().__init__(
            message,
            exit_code=1,
            entity_type=entity_type,
            entity_id=entity_id,
        )


class IntegrityError(RepositoryError):
    """
    Exception raised for database integrity violations.

    This is raised for foreign key violations, NOT NULL constraints,
    check constraints, and other database integrity issues.

    Attributes:
        message: Human-readable error message.
        constraint: Optional constraint name that was violated.

    Example:
        ```python
        try:
            self.db.execute("INSERT INTO history ...")
        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Database integrity violation: {e}",
                constraint="fk_history_manifest",
            ) from e
        ```
    """

    def __init__(
        self,
        message: str = "Database integrity violation",
        constraint: str | None = None,
    ) -> None:
        """
        Initialize an IntegrityError.

        Args:
            message: Human-readable error message.
            constraint: Optional constraint name that was violated.
        """
        super().__init__(message, exit_code=1)
        self.constraint = constraint

    def __repr__(self) -> str:
        """Return a repr string for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"exit_code={self.exit_code}, "
            f"constraint={self.constraint!r}"
            ")"
        )


class DataError(RepositoryError):
    """
    Exception raised for data validation errors.

    This is raised when entity data fails validation before
    being persisted to the database.

    Attributes:
        message: Human-readable error message.
        field: Optional field name that failed validation.
        value: Optional invalid value.

    Example:
        ```python
        def create(self, entry: HistoryEntry) -> str:
            if not entry.id:
                raise DataError(
                    "History entry ID cannot be empty",
                    field="id",
                    value=entry.id,
                )
            if len(entry.mode) > 50:
                raise DataError(
                    "Mode exceeds maximum length",
                    field="mode",
                    value=entry.mode,
                )
            # ... create logic
        ```
    """

    def __init__(
        self,
        message: str = "Data validation error",
        field: str | None = None,
        value: object | None = None,
    ) -> None:
        """
        Initialize a DataError.

        Args:
            message: Human-readable error message.
            field: Optional field name that failed validation.
            value: Optional invalid value.
        """
        super().__init__(message, exit_code=1)
        self.field = field
        self.value = value

    def __repr__(self) -> str:
        """Return a repr string for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"exit_code={self.exit_code}, "
            f"field={self.field!r}, "
            f"value={self.value!r}"
            ")"
        )


class OptimisticLockError(RepositoryError):
    """
    Exception raised for optimistic locking failures.

    This is raised when an update fails due to concurrent
    modification (e.g., version mismatch).

    Attributes:
        message: Human-readable error message.
        entity_type: The type of entity that had a conflict.
        entity_id: The ID of the conflicting entity.
        expected_version: The expected version number.
        actual_version: The actual version number found.

    Example:
        ```python
        def update(self, id: str, version: int, **kwargs: Any) -> bool:
            current = self.get_by_id(id)
            if current is None:
                return False
            if current.version != version:
                raise OptimisticLockError(
                    "Concurrent modification detected",
                    entity_type=self.model_class.__name__,
                    entity_id=id,
                    expected_version=version,
                    actual_version=current.version,
                )
            # ... update logic
        ```
    """

    def __init__(
        self,
        message: str = "Optimistic lock failure",
        entity_type: str | None = None,
        entity_id: str | None = None,
        expected_version: int | None = None,
        actual_version: int | None = None,
    ) -> None:
        """
        Initialize an OptimisticLockError.

        Args:
            message: Human-readable error message.
            entity_type: The type of entity that had a conflict.
            entity_id: The ID of the conflicting entity.
            expected_version: The expected version number.
            actual_version: The actual version number found.
        """
        super().__init__(
            message,
            exit_code=1,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.expected_version = expected_version
        self.actual_version = actual_version

    def __repr__(self) -> str:
        """Return a repr string for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"exit_code={self.exit_code}, "
            f"entity_type={self.entity_type!r}, "
            f"entity_id={self.entity_id!r}, "
            f"expected_version={self.expected_version!r}, "
            f"actual_version={self.actual_version!r}"
            ")"
        )


__all__ = [
    "DataError",
    "DuplicateError",
    "IntegrityError",
    "NotFoundError",
    "OptimisticLockError",
    "RepositoryError",
]
