# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Manifest repository for DMLClean.

CRUD operations for deletion manifest index following the Repository Pattern.

Example:
    ```python
    from dmlclean.storage import get_database, ManifestRepository

    db = get_database()
    repo = ManifestRepository(db)

    # Create manifest index
    repo.create(
        id="abc123",
        manifest_path="/path/to/manifest.json",
        file_count=150,
        size_bytes=1024*1024*50,
    )

    # Get by ID
    record = repo.get_by_id("abc123")

    # Mark as undone
    repo.mark_undone("abc123")

    # List all
    records = repo.list_all()
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
class ManifestRecord:
    """
    A deletion manifest index record.

    Attributes:
        id: Unique identifier (UUID, matches history.id).
        manifest_path: Path to JSON manifest file.
        created_at: ISO 8601 timestamp.
        file_count: Number of files in manifest.
        size_bytes: Total size in bytes.
        undone: Whether manifest was undone.
        undone_at: ISO 8601 timestamp of undo.
        notes: Optional notes.
    """

    id: str
    manifest_path: str
    created_at: str
    file_count: int = 0
    size_bytes: int = 0
    undone: bool = False
    undone_at: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "manifest_path": self.manifest_path,
            "created_at": self.created_at,
            "file_count": self.file_count,
            "size_bytes": self.size_bytes,
            "undone": self.undone,
            "undone_at": self.undone_at,
            "notes": self.notes,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> ManifestRecord:
        """Create ManifestRecord from database row."""
        return cls(
            id=row["id"],
            manifest_path=row["manifest_path"],
            created_at=row["created_at"],
            file_count=row["file_count"] or 0,
            size_bytes=row["size_bytes"] or 0,
            undone=bool(row["undone"]),
            undone_at=row["undone_at"],
            notes=row["notes"] or "",
        )


class ManifestRepository(Repository[ManifestRecord]):
    """
    Repository for deletion manifest index CRUD operations.

    Implements the Repository Pattern for tracking manifest files
    stored in the history/manifests/ directory.

    Attributes:
        db: Database instance.

    Example:
        ```python
        db = get_database()
        repo = ManifestRepository(db)

        # Create
        record = repo.create(
            id="abc123",
            manifest_path="/path/to/manifest.json",
            file_count=150,
        )

        # Get
        record = repo.get_by_id("abc123")

        # Mark as undone
        repo.mark_undone("abc123")

        # List not undone
        records = repo.list_undone()
        ```
    """

    def __init__(self, db: Database) -> None:
        """
        Initialize the manifest repository.

        Args:
            db: Database instance.
        """
        super().__init__(ManifestRecord)
        self.db = db
        logger.debug("ManifestRepository initialized")

    def create(
        self,
        id: str,  # noqa: A002
        manifest_path: str,
        created_at: str,
        file_count: int = 0,
        size_bytes: int = 0,
        notes: str = "",
    ) -> ManifestRecord:
        """
        Create a new manifest index record.

        Args:
            id: Unique identifier (UUID).
            manifest_path: Path to JSON manifest file.
            created_at: ISO 8601 timestamp.
            file_count: Number of files in manifest.
            size_bytes: Total size in bytes.
            notes: Optional notes.

        Returns:
            ManifestRecord: Created record.

        Raises:
            DuplicateError: If manifest with ID already exists.
            DataError: If data validation fails.
            IntegrityError: If database integrity constraint violated.
            RepositoryError: If database error occurs.
        """
        # Validate required fields
        if not id:
            raise DataError("Manifest ID cannot be empty", field="id", value=id)
        if not manifest_path:
            raise DataError(
                "Manifest path cannot be empty", field="manifest_path", value=manifest_path
            )

        # Check for duplicate
        if self.exists(id):
            raise DuplicateError(
                "Manifest already exists",
                entity_type="ManifestRecord",
                entity_id=id,
            )

        try:
            with self.db.transaction():
                self.db.execute(
                    """
                    INSERT INTO manifests (
                        id, manifest_path, created_at, file_count, size_bytes, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (id, manifest_path, created_at, file_count, size_bytes, notes),
                )
        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Database integrity violation: {e}",
                constraint="manifests_pkey",
            ) from e
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

        logger.info(f"Manifest index created: {id}")

        return ManifestRecord(
            id=id,
            manifest_path=manifest_path,
            created_at=created_at,
            file_count=file_count,
            size_bytes=size_bytes,
            notes=notes,
        )

    def get_by_id(self, id: str) -> ManifestRecord | None:  # noqa: A002
        """
        Get a manifest record by ID.

        Args:
            id: Record identifier.

        Returns:
            ManifestRecord | None: Record if found.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT * FROM manifests WHERE id = ?",
                (id,),
            )
            return ManifestRecord.from_row(row) if row else None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        undone: bool | None = None,
    ) -> list[ManifestRecord]:
        """
        List manifest records.

        Args:
            limit: Maximum entries to return.
            offset: Offset for pagination.
            undone: Filter by undone status.

        Returns:
            list[ManifestRecord]: List of records.

        Raises:
            RepositoryError: If database error occurs.
        """
        query = "SELECT * FROM manifests WHERE 1=1"
        params: list[Any] = []

        if undone is not None:
            query += " AND undone = ?"
            params.append(1 if undone else 0)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            rows = self.db.fetchall(query, params)
            return [ManifestRecord.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def update(
        self,
        id: str,  # noqa: A002
        manifest_path: str | None = None,
        file_count: int | None = None,
        size_bytes: int | None = None,
        notes: str | None = None,
    ) -> bool:
        """
        Update a manifest record.

        Args:
            id: Record identifier.
            manifest_path: New path.
            file_count: New file count.
            size_bytes: New size.
            notes: New notes.

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
                "manifest_path": manifest_path,
                "file_count": file_count,
                "size_bytes": size_bytes,
                "notes": notes,
            }.items()
            if v is not None
        }

        if not updates:
            raise DataError(
                "No valid fields to update",
                field="kwargs",
                value=list(updates.keys()),
            )

        if not self.exists(id):
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values())
        values.append(id)

        try:
            with self.db.transaction():
                query = f"UPDATE manifests SET {set_clause} WHERE id = ?"  # noqa: S608
                self.db.execute(query, values)
            logger.info(f"Manifest updated: {id}")
            return True
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def delete(self, id: str) -> bool:  # noqa: A002
        """
        Delete a manifest record.

        Args:
            id: Record identifier.

        Returns:
            bool: True if deleted.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            with self.db.transaction():
                cursor = self.db.execute(
                    "DELETE FROM manifests WHERE id = ?",
                    (id,),
                )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Manifest deleted: {id}")
            return deleted
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def exists(self, id: str) -> bool:  # noqa: A002
        """
        Check if a manifest record exists.

        Args:
            id: Record identifier.

        Returns:
            bool: True if exists.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT 1 FROM manifests WHERE id = ?",
                (id,),
            )
            return row is not None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def count(self) -> int:
        """
        Count total manifest records.

        Returns:
            int: Total count.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone("SELECT COUNT(*) as cnt FROM manifests")
            return row["cnt"] if row else 0
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def mark_undone(self, id: str) -> bool:
        """
        Mark a manifest as undone.

        Args:
            id: Record identifier.

        Returns:
            bool: True if updated.

        Raises:
            RepositoryError: If database error occurs.
        """
        now = datetime.now(UTC).isoformat()

        try:
            with self.db.transaction():
                self.db.execute(
                    """
                    UPDATE manifests
                    SET undone = 1, undone_at = ?
                    WHERE id = ?
                    """,
                    (now, id),
                )
            logger.info(f"Manifest marked as undone: {id}")
            return True
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def list_undone(self, limit: int = 100) -> list[ManifestRecord]:
        """
        List undone manifest records.

        Args:
            limit: Maximum entries to return.

        Returns:
            list[ManifestRecord]: List of undone records.

        Raises:
            RepositoryError: If database error occurs.
        """
        return self.list_all(limit=limit, undone=True)

    def list_pending(self, limit: int = 100) -> list[ManifestRecord]:
        """
        List manifest records that haven't been undone.

        Args:
            limit: Maximum entries to return.

        Returns:
            list[ManifestRecord]: List of pending records.

        Raises:
            RepositoryError: If database error occurs.
        """
        return self.list_all(limit=limit, undone=False)


__all__ = ["ManifestRecord", "ManifestRepository"]
