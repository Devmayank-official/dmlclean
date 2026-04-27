"""
History repository for DMLClean.

CRUD operations for cleaning history entries following the Repository Pattern.

Example:
    ```python
    from dmlclean.storage import get_database, HistoryRepository

    db = get_database()
    repo = HistoryRepository(db)

    # Create entry
    entry = repo.create(
        id="abc123",
        mode="trash",
        profile="developer",
        scan_mode="fast",
        files_found=150,
        files_deleted=145,
        size_bytes=1024*1024*50,
        duration_ms=2500,
    )

    # Get entry
    entry = repo.get_by_id("abc123")

    # List recent entries
    entries = repo.list_all(limit=10)

    # Delete entry
    repo.delete("abc123")
    ```
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
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
class HistoryEntry:
    """
    A cleaning history entry.

    Attributes:
        id: Unique identifier (UUID).
        timestamp: ISO 8601 timestamp of operation.
        mode: Clean mode (dry-run, trash, permanent).
        profile: Cleaning profile used.
        scan_mode: Scan mode used (fast, deep, custom).
        files_found: Number of files found during scan.
        files_deleted: Number of files actually deleted.
        size_bytes: Total size in bytes.
        duration_ms: Operation duration in milliseconds.
        categories: List of categories cleaned.
        status: Operation status (complete, partial, failed).
        error_message: Error details if failed.
    """

    id: str
    timestamp: str
    mode: str
    profile: str
    scan_mode: str
    files_found: int = 0
    files_deleted: int = 0
    size_bytes: int = 0
    duration_ms: int = 0
    categories: list[str] = field(default_factory=list)
    status: str = "complete"
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "profile": self.profile,
            "scan_mode": self.scan_mode,
            "files_found": self.files_found,
            "files_deleted": self.files_deleted,
            "size_bytes": self.size_bytes,
            "duration_ms": self.duration_ms,
            "categories": self.categories,
            "status": self.status,
            "error_message": self.error_message,
        }

    @property
    def size_human(self) -> str:
        """Get human-readable size."""
        from dmlclean.utils.sizes import humanize_size

        return humanize_size(self.size_bytes)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> HistoryEntry:
        """Create HistoryEntry from database row."""
        categories = json.loads(row["categories"]) if row["categories"] else []
        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            mode=row["mode"],
            profile=row["profile"] or "default",
            scan_mode=row["scan_mode"],
            files_found=row["files_found"],
            files_deleted=row["files_deleted"],
            size_bytes=row["size_bytes"],
            duration_ms=row["duration_ms"],
            categories=categories,
            status=row["status"],
            error_message=row["error_message"],
        )


class HistoryRepository(Repository[HistoryEntry]):
    """
    Repository for cleaning history CRUD operations.

    Implements the Repository Pattern with full CRUD operations,
    pagination, and filtering support.

    Attributes:
        db: Database instance.

    Example:
        ```python
        db = get_database()
        repo = HistoryRepository(db)

        # Create
        entry = repo.create(
            id="abc123",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=150,
        )

        # Read
        entry = repo.get_by_id("abc123")

        # Update
        repo.update("abc123", status="failed", error_message="Disk full")

        # Delete
        repo.delete("abc123")

        # List with filters
        entries = repo.list_all(limit=10, profile="developer", status="complete")
        ```
    """

    def __init__(self, db: Database) -> None:
        """
        Initialize the history repository.

        Args:
            db: Database instance.
        """
        super().__init__(HistoryEntry)
        self.db = db
        logger.debug("HistoryRepository initialized")

    def create(
        self,
        id: str,  # noqa: A002
        mode: str,
        profile: str,
        scan_mode: str,
        files_found: int = 0,
        files_deleted: int = 0,
        size_bytes: int = 0,
        duration_ms: int = 0,
        categories: list[str] | None = None,
        status: str = "complete",
        error_message: str | None = None,
    ) -> HistoryEntry:
        """
        Create a new history entry.

        Args:
            id: Unique identifier (UUID).
            mode: Clean mode.
            profile: Cleaning profile.
            scan_mode: Scan mode.
            files_found: Files found during scan.
            files_deleted: Files actually deleted.
            size_bytes: Total size.
            duration_ms: Duration in milliseconds.
            categories: Categories cleaned.
            status: Operation status.
            error_message: Error message if failed.

        Returns:
            HistoryEntry: Created entry.

        Raises:
            DuplicateError: If entry with ID already exists.
            DataError: If data validation fails.
            IntegrityError: If database integrity constraint violated.
            RepositoryError: If database error occurs.
        """
        # Validate required fields
        if not id:
            raise DataError("History entry ID cannot be empty", field="id", value=id)
        if not mode:
            raise DataError("Mode cannot be empty", field="mode", value=mode)
        if mode not in ("dry-run", "trash", "permanent"):
            raise DataError(
                f"Invalid mode: {mode}. Must be 'dry-run', 'trash', or 'permanent'",
                field="mode",
                value=mode,
            )

        # Check for duplicate
        if self.exists(id):
            raise DuplicateError(
                "History entry already exists",
                entity_type="HistoryEntry",
                entity_id=id,
            )

        timestamp = datetime.now(UTC).isoformat()
        categories_json = json.dumps(categories or [])

        try:
            with self.db.transaction():
                self.db.execute(
                    """
                    INSERT INTO history (
                        id, timestamp, mode, profile, scan_mode,
                        files_found, files_deleted, size_bytes, duration_ms,
                        categories, status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        id,
                        timestamp,
                        mode,
                        profile,
                        scan_mode,
                        files_found,
                        files_deleted,
                        size_bytes,
                        duration_ms,
                        categories_json,
                        status,
                        error_message,
                    ),
                )
        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Database integrity violation: {e}",
                constraint="history_pkey",
            ) from e
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

        logger.info(f"History entry created: {id} ({status})")

        return HistoryEntry(
            id=id,
            timestamp=timestamp,
            mode=mode,
            profile=profile,
            scan_mode=scan_mode,
            files_found=files_found,
            files_deleted=files_deleted,
            size_bytes=size_bytes,
            duration_ms=duration_ms,
            categories=categories or [],
            status=status,
            error_message=error_message,
        )

    def get_by_id(self, id: str) -> HistoryEntry | None:  # noqa: A002
        """
        Get a history entry by ID.

        Args:
            id: Entry identifier.

        Returns:
            HistoryEntry | None: Entry if found.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT * FROM history WHERE id = ?",
                (id,),
            )
            return HistoryEntry.from_row(row) if row else None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        profile: str | None = None,
        status: str | None = None,
        mode: str | None = None,
    ) -> list[HistoryEntry]:
        """
        List history entries with optional filters.

        Args:
            limit: Maximum entries to return.
            offset: Offset for pagination.
            profile: Filter by profile.
            status: Filter by status.
            mode: Filter by mode.

        Returns:
            list[HistoryEntry]: List of entries.

        Raises:
            RepositoryError: If database error occurs.
        """
        query = "SELECT * FROM history WHERE 1=1"
        params: list[Any] = []

        if profile:
            query += " AND profile = ?"
            params.append(profile)
        if status:
            query += " AND status = ?"
            params.append(status)
        if mode:
            query += " AND mode = ?"
            params.append(mode)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            rows = self.db.fetchall(query, params)
            return [HistoryEntry.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def update(self, id: str, **kwargs: Any) -> bool:  # noqa: A002
        """
        Update a history entry.

        Args:
            id: Entry identifier.
            **kwargs: Fields to update (status, error_message, etc.).

        Returns:
            bool: True if updated, False if not found.

        Raises:
            RepositoryError: If database error occurs.
            DataError: If no valid fields provided.

        Example:
            ```python
            # Update status and error message
            repo.update(
                "abc123",
                status="failed",
                error_message="Disk full"
            )

            # Update files_deleted count
            repo.update("abc123", files_deleted=150)
            ```
        """
        # Valid fields that can be updated
        valid_fields = {
            "status",
            "error_message",
            "files_found",
            "files_deleted",
            "size_bytes",
            "duration_ms",
            "categories",
        }

        # Filter to valid fields
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not updates:
            raise DataError(
                f"No valid fields to update. Valid fields: {valid_fields}",
                field="kwargs",
                value=list(kwargs.keys()),
            )

        # Check if entry exists
        if not self.exists(id):
            return False

        # Build UPDATE query
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())

        # Handle categories JSON conversion
        values = []
        for k, v in updates.items():
            if k == "categories" and isinstance(v, list):
                values.append(json.dumps(v))
            else:
                values.append(v)
        values.append(id)

        try:
            with self.db.transaction():
                self.db.execute(
                    f"UPDATE history SET {set_clause} WHERE id = ?",
                    values,
                )
            logger.info(f"History entry updated: {id}")
            return True
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def delete(self, id: str) -> bool:  # noqa: A002
        """
        Delete a history entry.

        Args:
            id: Entry identifier.

        Returns:
            bool: True if deleted, False if not found.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            with self.db.transaction():
                cursor = self.db.execute(
                    "DELETE FROM history WHERE id = ?",
                    (id,),
                )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"History entry deleted: {id}")
            return deleted
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def exists(self, id: str) -> bool:  # noqa: A002
        """
        Check if a history entry exists.

        Args:
            id: Entry identifier.

        Returns:
            bool: True if exists.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT 1 FROM history WHERE id = ?",
                (id,),
            )
            return row is not None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def count(self) -> int:
        """
        Count total history entries.

        Returns:
            int: Total count.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone("SELECT COUNT(*) as cnt FROM history")
            return row["cnt"] if row else 0
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def get_summary(
        self,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get summary statistics for history.

        Args:
            days: Number of days to summarize.

        Returns:
            dict[str, Any]: Summary statistics.
        """
        row = self.db.fetchone(
            """
            SELECT
                COUNT(*) as total_operations,
                SUM(files_deleted) as total_files_deleted,
                SUM(size_bytes) as total_size_bytes,
                AVG(duration_ms) as avg_duration_ms,
                SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM history
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            """,
            (days,),
        )

        if not row:
            return {
                "total_operations": 0,
                "total_files_deleted": 0,
                "total_size_bytes": 0,
                "avg_duration_ms": 0,
                "successful": 0,
                "failed": 0,
            }

        return {
            "total_operations": row["total_operations"] or 0,
            "total_files_deleted": row["total_files_deleted"] or 0,
            "total_size_bytes": row["total_size_bytes"] or 0,
            "avg_duration_ms": row["avg_duration_ms"] or 0,
            "successful": row["successful"] or 0,
            "failed": row["failed"] or 0,
        }

    def delete(self, entry_id: str) -> bool:
        """
        Delete a history entry.

        Args:
            entry_id: Entry identifier.

        Returns:
            bool: True if deleted.
        """
        cursor = self.conn.execute(
            "DELETE FROM history WHERE id = ?",
            (entry_id,),
        )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"History entry deleted: {entry_id}")
        return deleted

    def clear_all(self) -> int:
        """
        Clear all history entries.

        Returns:
            int: Number of entries deleted.
        """
        cursor = self.conn.execute("DELETE FROM history")
        count = cursor.rowcount
        logger.info(f"Cleared {count} history entries")
        return count

    def get_by_profile(self, profile: str, limit: int = 10) -> list[HistoryEntry]:
        """
        Get history entries by profile.

        Args:
            profile: Profile name.
            limit: Maximum entries to return.

        Returns:
            list[HistoryEntry]: List of entries.
        """
        rows = self.conn.execute(
            "SELECT * FROM history WHERE profile = ? ORDER BY timestamp DESC LIMIT ?",
            (profile, limit),
        ).fetchall()

        return [HistoryEntry.from_row(row) for row in rows]

    def get_failed(self, limit: int = 10) -> list[HistoryEntry]:
        """
        Get failed history entries.

        Args:
            limit: Maximum entries to return.

        Returns:
            list[HistoryEntry]: List of failed entries.
        """
        rows = self.conn.execute(
            "SELECT * FROM history WHERE status = 'failed' ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()

        return [HistoryEntry.from_row(row) for row in rows]
