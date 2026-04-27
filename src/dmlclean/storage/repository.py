# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Generic Repository Pattern for DMLClean.

This module provides the abstract base class for all repository implementations
following the Repository Pattern with Generic type support.

Example:
    ```python
    from dmlclean.storage.repository import Repository
    from dmlclean.models.history import HistoryEntry

    class HistoryRepository(Repository[HistoryEntry]):
        def get_by_id(self, id: str) -> HistoryEntry | None:
            # Implementation here
            ...
    ```
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar

from dmlclean.exceptions.repository import NotFoundError

# Type variable for entity type
T = TypeVar("T")


class RepositoryProtocol(Protocol[T]):
    """
    Protocol defining the repository interface.

    This protocol specifies the minimum interface that all repositories
    must implement. Use this for type hints when you don't need the
    full base class.

    Type Parameter:
        T: The entity type this repository manages.

    Example:
        ```python
        def get_history(repo: RepositoryProtocol[HistoryEntry], id: str) -> None:
            entry = repo.get_by_id(id)
            if entry:
                print(f"Found: {entry.id}")
        ```
    """

    def get_by_id(self, id: str) -> T | None:
        """
        Get an entity by its unique ID.

        Args:
            id: The unique identifier of the entity.

        Returns:
            The entity if found, None otherwise.
        """
        ...

    def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """
        List all entities with pagination.

        Args:
            limit: Maximum number of entities to return.
            offset: Number of entities to skip.

        Returns:
            List of entities.
        """
        ...

    def create(self, entity: T) -> str:
        """
        Create a new entity.

        Args:
            entity: The entity to create.

        Returns:
            The unique ID of the created entity.
        """
        ...

    def update(self, id: str, **kwargs: Any) -> bool:
        """
        Update an existing entity.

        Args:
            id: The unique identifier of the entity to update.
            **kwargs: Fields to update.

        Returns:
            True if the entity was updated, False if not found.
        """
        ...

    def delete(self, id: str) -> bool:
        """
        Delete an entity by ID.

        Args:
            id: The unique identifier of the entity to delete.

        Returns:
            True if the entity was deleted, False if not found.
        """
        ...

    def exists(self, id: str) -> bool:
        """
        Check if an entity exists.

        Args:
            id: The unique identifier to check.

        Returns:
            True if the entity exists, False otherwise.
        """
        ...

    def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count of entities.
        """
        ...


class Repository(ABC, Generic[T]):
    """
    Abstract base class for all DMLClean repositories.

    This class implements the Repository Pattern with Generic type support,
    providing a consistent interface for data access across the application.

    All repositories must inherit from this class and implement the
    abstract methods.

    Type Parameter:
        T: The entity type this repository manages.

    Attributes:
        model_class: The entity class this repository manages.

    Example:
        ```python
        from dmlclean.storage.repository import Repository
        from dmlclean.models.history import HistoryEntry
        from dmlclean.storage.database import Database

        class HistoryRepository(Repository[HistoryEntry]):
            def __init__(self, db: Database):
                super().__init__(HistoryEntry)
                self.db = db

            def get_by_id(self, id: str) -> HistoryEntry | None:
                row = self.db.fetchone(
                    "SELECT * FROM history WHERE id = ?",
                    (id,)
                )
                if row is None:
                    return None
                return HistoryEntry.from_row(row)

            def list_all(self, limit: int = 100, offset: int = 0) -> list[HistoryEntry]:
                rows = self.db.fetchall(
                    "SELECT * FROM history ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
                return [HistoryEntry.from_row(row) for row in rows]

            def create(self, entry: HistoryEntry) -> str:
                with self.db.transaction():
                    self.db.execute(
                        "INSERT INTO history (id, timestamp, mode, ...) VALUES (?, ?, ?, ...)",
                        (entry.id, entry.timestamp, entry.mode, ...)
                    )
                return entry.id

            def update(self, id: str, **kwargs: Any) -> bool:
                if not self.exists(id):
                    return False
                set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
                values = list(kwargs.values()) + [id]
                with self.db.transaction():
                    self.db.execute(
                        f"UPDATE history SET {set_clause} WHERE id = ?",
                        values
                    )
                return True

            def delete(self, id: str) -> bool:
                if not self.exists(id):
                    return False
                with self.db.transaction():
                    self.db.execute("DELETE FROM history WHERE id = ?", (id,))
                return True

            def exists(self, id: str) -> bool:
                row = self.db.fetchone(
                    "SELECT 1 FROM history WHERE id = ?",
                    (id,)
                )
                return row is not None

            def count(self) -> int:
                row = self.db.fetchone("SELECT COUNT(*) as cnt FROM history")
                return row["cnt"] if row else 0
        ```
    """

    def __init__(self, model_class: type[T]) -> None:
        """
        Initialize the repository.

        Args:
            model_class: The entity class this repository manages.
        """
        self.model_class = model_class

    @abstractmethod
    def get_by_id(self, id: str) -> T | None:
        """
        Get an entity by its unique ID.

        Args:
            id: The unique identifier of the entity.

        Returns:
            The entity if found, None otherwise.

        Raises:
            RepositoryError: If database error occurs.
        """
        pass

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """
        List all entities with pagination.

        Args:
            limit: Maximum number of entities to return.
            offset: Number of entities to skip.

        Returns:
            List of entities.

        Raises:
            RepositoryError: If database error occurs.
        """
        pass

    @abstractmethod
    def create(self, entity: T) -> str:
        """
        Create a new entity.

        Args:
            entity: The entity to create.

        Returns:
            The unique ID of the created entity.

        Raises:
            RepositoryError: If database error occurs.
            DuplicateError: If entity with same ID already exists.
        """
        pass

    @abstractmethod
    def update(self, id: str, **kwargs: Any) -> bool:
        """
        Update an existing entity.

        Args:
            id: The unique identifier of the entity to update.
            **kwargs: Fields to update.

        Returns:
            True if the entity was updated, False if not found.

        Raises:
            RepositoryError: If database error occurs.
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete an entity by ID.

        Args:
            id: The unique identifier of the entity to delete.

        Returns:
            True if the entity was deleted, False if not found.

        Raises:
            RepositoryError: If database error occurs.
        """
        pass

    @abstractmethod
    def exists(self, id: str) -> bool:
        """
        Check if an entity exists.

        Args:
            id: The unique identifier to check.

        Returns:
            True if the entity exists, False otherwise.

        Raises:
            RepositoryError: If database error occurs.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count of entities.

        Raises:
            RepositoryError: If database error occurs.
        """
        pass

    def get_or_raise(self, id: str) -> T:
        """
        Get an entity by ID or raise NotFoundError.

        This is a convenience method that combines get_by_id with
        error handling.

        Args:
            id: The unique identifier of the entity.

        Returns:
            The entity if found.

        Raises:
            NotFoundError: If the entity is not found.
            RepositoryError: If database error occurs.

        Example:
            ```python
            # Instead of:
            entry = repo.get_by_id(id)
            if entry is None:
                raise NotFoundError(f"Entry not found: {id}")

            # Use:
            entry = repo.get_or_raise(id)
            ```
        """
        entity = self.get_by_id(id)
        if entity is None:
            raise NotFoundError(f"{self.model_class.__name__} not found: {id}")
        return entity

    def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> list[T]:
        """
        List entities with page-based pagination.

        This is a convenience method that converts page/page_size
        to offset/limit.

        Args:
            page: Page number (1-indexed).
            page_size: Number of entities per page.

        Returns:
            List of entities for the requested page.

        Example:
            ```python
            # Get page 3 with 20 items per page
            items = repo.list_paginated(page=3, page_size=20)
            # Equivalent to:
            # items = repo.list_all(limit=20, offset=40)
            ```
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1
        offset = (page - 1) * page_size
        return self.list_all(limit=page_size, offset=offset)

    def get_total_pages(self, page_size: int = 20) -> int:
        """
        Get total number of pages.

        Args:
            page_size: Number of entities per page.

        Returns:
            Total number of pages (rounded up).
        """
        if page_size < 1:
            page_size = 1
        total = self.count()
        return (total + page_size - 1) // page_size


__all__ = [
    "Repository",
    "RepositoryProtocol",
    "T",
]
