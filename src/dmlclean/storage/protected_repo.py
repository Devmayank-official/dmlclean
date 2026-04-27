# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Protected repository for DMLClean.

CRUD operations for protected zone entries following the Repository Pattern.

Example:
    ```python
    from dmlclean.storage import get_database, ProtectedRepository

    db = get_database()
    repo = ProtectedRepository(db)

    # Add protected path
    repo.create(
        id="abc123",
        path="/home/user/important-project",
        description="My important project",
        is_glob=False,
    )

    # Check if path exists
    exists = repo.exists_by_path("/home/user/important-project")

    # List all protected paths
    paths = repo.list_all()

    # Remove protection
    repo.delete("abc123")
    ```
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from dmlclean.exceptions.repository import (
    DataError,
    DuplicateError,
    IntegrityError,
    RepositoryError,
)
from dmlclean.storage.database import Database
from dmlclean.storage.repository import Repository


@dataclass
class ProtectedPathEntry:
    """
    A protected path entry.

    Attributes:
        id: Unique identifier (UUID).
        path: Protected path or glob pattern.
        description: Human-readable description.
        is_glob: Whether the path is a glob pattern.
        created_at: ISO 8601 timestamp.
        updated_at: ISO 8601 timestamp.
    """

    id: str
    path: str
    description: str = ""
    is_glob: bool = False
    created_at: str = ""
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "path": self.path,
            "description": self.description,
            "is_glob": self.is_glob,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> ProtectedPathEntry:
        """Create ProtectedPathEntry from database row."""
        return cls(
            id=row["id"],
            path=row["path"],
            description=row["description"] or "",
            is_glob=bool(row["is_glob"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class ProtectedRepository(Repository[ProtectedPathEntry]):
    """
    Repository for protected zone CRUD operations.

    Implements the Repository Pattern with full CRUD operations
    for managing protected paths and glob patterns.

    Attributes:
        db: Database instance.

    Example:
        ```python
        db = get_database()
        repo = ProtectedRepository(db)

        # Add protected path
        entry = repo.create(
            id="abc123",
            path="/home/user/important",
            description="Important files",
        )

        # Get by ID
        entry = repo.get_by_id("abc123")

        # Check by path
        entry = repo.get_by_path("/home/user/important")

        # List all
        entries = repo.list_all()

        # Delete
        repo.delete("abc123")
        ```
    """

    def __init__(self, db: Database) -> None:
        """
        Initialize the protected repository.

        Args:
            db: Database instance.
        """
        super().__init__(ProtectedPathEntry)
        self.db = db
        logger.debug("ProtectedRepository initialized")

    def create(
        self,
        id: str,  # noqa: A002
        path: str,
        description: str = "",
        is_glob: bool = False,
    ) -> ProtectedPathEntry:
        """
        Create a new protected path entry.

        Args:
            id: Unique identifier (UUID).
            path: Protected path or glob pattern.
            description: Human-readable description.
            is_glob: Whether the path is a glob pattern.

        Returns:
            ProtectedPathEntry: Created entry.

        Raises:
            DuplicateError: If path already protected.
            DataError: If data validation fails.
            IntegrityError: If database integrity constraint violated.
            RepositoryError: If database error occurs.
        """
        # Validate required fields
        if not id:
            raise DataError("Protected path ID cannot be empty", field="id", value=id)
        if not path:
            raise DataError("Path cannot be empty", field="path", value=path)

        # Check for duplicate path
        if self.exists_by_path(path):
            raise DuplicateError(
                f"Path already protected: {path}",
                entity_type="ProtectedPathEntry",
                entity_id=path,
            )

        now = datetime.now(UTC).isoformat()

        try:
            with self.db.transaction():
                self.db.execute(
                    """
                    INSERT INTO protected_paths (
                        id, path, description, is_glob, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (id, path, description, 1 if is_glob else 0, now),
                )
        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Database integrity violation: {e}",
                constraint="protected_paths_pkey",
            ) from e
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

        logger.info(f"Protected path created: {id} ({path})")

        return ProtectedPathEntry(
            id=id,
            path=path,
            description=description,
            is_glob=is_glob,
            created_at=now,
        )

    def get_by_id(self, id: str) -> ProtectedPathEntry | None:  # noqa: A002
        """
        Get a protected path entry by ID.

        Args:
            id: Entry identifier.

        Returns:
            ProtectedPathEntry | None: Entry if found.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT * FROM protected_paths WHERE id = ?",
                (id,),
            )
            return ProtectedPathEntry.from_row(row) if row else None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def get_by_path(self, path: str) -> ProtectedPathEntry | None:
        """
        Get a protected path entry by path.

        Args:
            path: Path to look up.

        Returns:
            ProtectedPathEntry | None: Entry if found.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT * FROM protected_paths WHERE path = ?",
                (path,),
            )
            return ProtectedPathEntry.from_row(row) if row else None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        is_glob: bool | None = None,
    ) -> list[ProtectedPathEntry]:
        """
        List protected path entries.

        Args:
            limit: Maximum entries to return.
            offset: Offset for pagination.
            is_glob: Filter by glob status.

        Returns:
            list[ProtectedPathEntry]: List of entries.

        Raises:
            RepositoryError: If database error occurs.
        """
        query = "SELECT * FROM protected_paths WHERE 1=1"
        params: list[Any] = []

        if is_glob is not None:
            query += " AND is_glob = ?"
            params.append(1 if is_glob else 0)

        query += " ORDER BY path ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            rows = self.db.fetchall(query, params)
            return [ProtectedPathEntry.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def update(
        self,
        id: str,  # noqa: A002
        path: str | None = None,
        description: str | None = None,
        is_glob: bool | None = None,
    ) -> bool:
        """
        Update a protected path entry.

        Args:
            id: Entry identifier.
            path: New path.
            description: New description.
            is_glob: New glob status.

        Returns:
            bool: True if updated.

        Raises:
            RepositoryError: If database error occurs.
            DataError: If no valid fields provided.
        """
        # Filter to valid fields
        updates = {
            k: v
            for k, v in {
                "path": path,
                "description": description,
                "is_glob": is_glob,
            }.items()
            if v is not None
        }

        if not updates:
            raise DataError(
                "No valid fields to update",
                field="kwargs",
                value=list(updates.keys()),
            )

        # Check if entry exists
        if not self.exists(id):
            return False

        # Build UPDATE query
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values())

        if "is_glob" in updates:
            values = [1 if v else 0 if isinstance(v, bool) else v for v in values]

        set_clause += ", updated_at = ?"
        values.append(datetime.now(UTC).isoformat())
        values.append(id)

        try:
            with self.db.transaction():
                query = f"UPDATE protected_paths SET {set_clause} WHERE id = ?"  # noqa: S608
                self.db.execute(query, values)
            logger.info(f"Protected path updated: {id}")
            return True
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def delete(self, id: str) -> bool:  # noqa: A002
        """
        Delete a protected path entry.

        Args:
            id: Entry identifier.

        Returns:
            bool: True if deleted.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            with self.db.transaction():
                cursor = self.db.execute(
                    "DELETE FROM protected_paths WHERE id = ?",
                    (id,),
                )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Protected path deleted: {id}")
            return deleted
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def exists(self, id: str) -> bool:  # noqa: A002
        """
        Check if a protected path entry exists by ID.

        Args:
            id: Entry identifier.

        Returns:
            bool: True if exists.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT 1 FROM protected_paths WHERE id = ?",
                (id,),
            )
            return row is not None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def exists_by_path(self, path: str) -> bool:
        """
        Check if a path is already protected.

        Args:
            path: Path to check.

        Returns:
            bool: True if protected.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT 1 FROM protected_paths WHERE path = ?",
                (path,),
            )
            return row is not None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def count(self) -> int:
        """
        Count total protected path entries.

        Returns:
            int: Total count.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone("SELECT COUNT(*) as cnt FROM protected_paths")
            return row["cnt"] if row else 0
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def clear_all(self) -> int:
        """
        Clear all protected path entries.

        Returns:
            int: Number of entries deleted.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            with self.db.transaction():
                cursor = self.db.execute("DELETE FROM protected_paths")
            count = cursor.rowcount
            logger.info(f"Cleared {count} protected paths")
            return count
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e


__all__ = ["ProtectedPathEntry", "ProtectedRepository"]
