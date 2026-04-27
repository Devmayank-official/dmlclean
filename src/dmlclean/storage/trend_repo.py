# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Trend repository for DMLClean.

CRUD operations for disk usage trend entries following the Repository Pattern.

Example:
    ```python
    from dmlclean.storage import get_database, TrendRepository

    db = get_database()
    repo = TrendRepository(db)

    # Record disk usage
    repo.create(
        mount_point="C:\\",
        total_bytes=1024*1024*1024*500,
        free_bytes=1024*1024*1024*200,
        used_bytes=1024*1024*1024*300,
    )

    # Get recent trends
    trends = repo.list_recent(days=30)

    # Get by mount point
    trends = repo.get_by_mount_point("C:\\")
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
    IntegrityError,
    RepositoryError,
)
from dmlclean.storage.database import Database
from dmlclean.storage.repository import Repository


@dataclass
class DiskTrendEntry:
    """
    A disk usage trend entry.

    Attributes:
        id: Auto-incrementing identifier.
        timestamp: ISO 8601 timestamp.
        mount_point: Mount point (e.g., "C:\\", "/", "/home").
        total_bytes: Total disk size in bytes.
        free_bytes: Free space in bytes.
        used_bytes: Used space in bytes.
        percent_used: Percentage of disk used.
    """

    id: int
    timestamp: str
    mount_point: str
    total_bytes: int = 0
    free_bytes: int = 0
    used_bytes: int = 0
    percent_used: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "mount_point": self.mount_point,
            "total_bytes": self.total_bytes,
            "free_bytes": self.free_bytes,
            "used_bytes": self.used_bytes,
            "percent_used": self.percent_used,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> DiskTrendEntry:
        """Create DiskTrendEntry from database row."""
        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            mount_point=row["mount_point"],
            total_bytes=row["total_bytes"] or 0,
            free_bytes=row["free_bytes"] or 0,
            used_bytes=row["used_bytes"] or 0,
            percent_used=row["percent_used"] or 0.0,
        )


class TrendRepository(Repository[DiskTrendEntry]):
    """
    Repository for disk usage trend CRUD operations.

    Implements the Repository Pattern for tracking disk usage
    over time for trend analysis.

    Attributes:
        db: Database instance.

    Example:
        ```python
        db = get_database()
        repo = TrendRepository(db)

        # Create
        entry = repo.create(
            mount_point="C:\\",
            total_bytes=500*1024**3,
            free_bytes=200*1024**3,
        )

        # List recent
        trends = repo.list_recent(days=30)

        # Get by mount point
        trends = repo.get_by_mount_point("C:\\")

        # Get summary
        summary = repo.get_summary(days=30)
        ```
    """

    def __init__(self, db: Database) -> None:
        """
        Initialize the trend repository.

        Args:
            db: Database instance.
        """
        super().__init__(DiskTrendEntry)
        self.db = db
        logger.debug("TrendRepository initialized")

    def create(
        self,
        mount_point: str,
        total_bytes: int,
        free_bytes: int,
        used_bytes: int | None = None,
        percent_used: float | None = None,
    ) -> DiskTrendEntry:
        """
        Create a new disk usage trend entry.

        Args:
            mount_point: Mount point (e.g., "C:\\", "/", "/home").
            total_bytes: Total disk size in bytes.
            free_bytes: Free space in bytes.
            used_bytes: Used space in bytes (calculated if None).
            percent_used: Percentage used (calculated if None).

        Returns:
            DiskTrendEntry: Created entry.

        Raises:
            DataError: If data validation fails.
            IntegrityError: If database integrity constraint violated.
            RepositoryError: If database error occurs.
        """
        # Validate required fields
        if not mount_point:
            raise DataError("Mount point cannot be empty", field="mount_point", value=mount_point)
        if total_bytes < 0:
            raise DataError(
                "Total bytes cannot be negative", field="total_bytes", value=total_bytes
            )
        if free_bytes < 0:
            raise DataError("Free bytes cannot be negative", field="free_bytes", value=free_bytes)

        # Calculate used_bytes and percent_used if not provided
        if used_bytes is None:
            used_bytes = total_bytes - free_bytes
        if percent_used is None:
            percent_used = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0.0

        timestamp = datetime.now(UTC).isoformat()

        try:
            with self.db.transaction():
                self.db.execute(
                    """
                    INSERT INTO disk_trend (
                        timestamp, mount_point, total_bytes, free_bytes,
                        used_bytes, percent_used
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (timestamp, mount_point, total_bytes, free_bytes, used_bytes, percent_used),
                )
        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Database integrity violation: {e}",
                constraint="disk_trend_pkey",
            ) from e
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

        # Get the auto-incremented ID
        row = self.db.fetchone("SELECT last_insert_rowid() as id")
        entry_id = row["id"] if row else 0

        logger.info(f"Disk trend recorded: {mount_point} ({percent_used:.1f}% used)")

        return DiskTrendEntry(
            id=entry_id,
            timestamp=timestamp,
            mount_point=mount_point,
            total_bytes=total_bytes,
            free_bytes=free_bytes,
            used_bytes=used_bytes,
            percent_used=percent_used,
        )

    def get_by_id(self, id: int) -> DiskTrendEntry | None:  # noqa: A002
        """
        Get a trend entry by ID.

        Args:
            id: Entry identifier.

        Returns:
            DiskTrendEntry | None: Entry if found.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT * FROM disk_trend WHERE id = ?",
                (id,),
            )
            return DiskTrendEntry.from_row(row) if row else None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        mount_point: str | None = None,
    ) -> list[DiskTrendEntry]:
        """
        List disk usage trend entries.

        Args:
            limit: Maximum entries to return.
            offset: Offset for pagination.
            mount_point: Filter by mount point.

        Returns:
            list[DiskTrendEntry]: List of entries.

        Raises:
            RepositoryError: If database error occurs.
        """
        query = "SELECT * FROM disk_trend WHERE 1=1"
        params: list[Any] = []

        if mount_point:
            query += " AND mount_point = ?"
            params.append(mount_point)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            rows = self.db.fetchall(query, params)
            return [DiskTrendEntry.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def update(
        self,
        id: int,  # noqa: A002
        total_bytes: int | None = None,
        free_bytes: int | None = None,
        used_bytes: int | None = None,
        percent_used: float | None = None,
    ) -> bool:
        """
        Update a trend entry.

        Args:
            id: Entry identifier.
            total_bytes: New total bytes.
            free_bytes: New free bytes.
            used_bytes: New used bytes.
            percent_used: New percent used.

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
                "total_bytes": total_bytes,
                "free_bytes": free_bytes,
                "used_bytes": used_bytes,
                "percent_used": percent_used,
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
                query = f"UPDATE disk_trend SET {set_clause} WHERE id = ?"  # noqa: S608
                self.db.execute(query, values)
            logger.info(f"Disk trend updated: {id}")
            return True
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def delete(self, id: int) -> bool:  # noqa: A002
        """
        Delete a trend entry.

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
                    "DELETE FROM disk_trend WHERE id = ?",
                    (id,),
                )
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Disk trend deleted: {id}")
            return deleted
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def exists(self, id: int) -> bool:  # noqa: A002
        """
        Check if a trend entry exists.

        Args:
            id: Entry identifier.

        Returns:
            bool: True if exists.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT 1 FROM disk_trend WHERE id = ?",
                (id,),
            )
            return row is not None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def count(self) -> int:
        """
        Count total trend entries.

        Returns:
            int: Total count.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone("SELECT COUNT(*) as cnt FROM disk_trend")
            return row["cnt"] if row else 0
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def list_recent(
        self,
        days: int = 30,
        mount_point: str | None = None,
        limit: int = 100,
    ) -> list[DiskTrendEntry]:
        """
        List recent trend entries.

        Args:
            days: Number of days to include.
            mount_point: Filter by mount point.
            limit: Maximum entries to return.

        Returns:
            list[DiskTrendEntry]: List of recent entries.

        Raises:
            RepositoryError: If database error occurs.
        """
        query = """
            SELECT * FROM disk_trend
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """
        params: list[Any] = [days]

        if mount_point:
            query += " AND mount_point = ?"
            params.append(mount_point)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            rows = self.db.fetchall(query, params)
            return [DiskTrendEntry.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def get_by_mount_point(
        self,
        mount_point: str,
        limit: int = 100,
    ) -> list[DiskTrendEntry]:
        """
        Get trend entries for a specific mount point.

        Args:
            mount_point: Mount point to filter by.
            limit: Maximum entries to return.

        Returns:
            list[DiskTrendEntry]: List of entries.

        Raises:
            RepositoryError: If database error occurs.
        """
        return self.list_all(limit=limit, mount_point=mount_point)

    def get_summary(self, days: int = 30) -> dict[str, Any]:
        """
        Get summary statistics for disk trends.

        Args:
            days: Number of days to summarize.

        Returns:
            dict[str, Any]: Summary statistics.

        Raises:
            RepositoryError: If database error occurs.
        """
        query = """
            SELECT
                COUNT(*) as total_entries,
                AVG(percent_used) as avg_percent_used,
                MAX(percent_used) as max_percent_used,
                MIN(percent_used) as min_percent_used,
                AVG(total_bytes) as avg_total_bytes,
                AVG(free_bytes) as avg_free_bytes,
                AVG(used_bytes) as avg_used_bytes
            FROM disk_trend
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """

        try:
            row = self.db.fetchone(query, (days,))
            if not row:
                return {
                    "total_entries": 0,
                    "avg_percent_used": 0.0,
                    "max_percent_used": 0.0,
                    "min_percent_used": 0.0,
                    "avg_total_bytes": 0,
                    "avg_free_bytes": 0,
                    "avg_used_bytes": 0,
                }

            return {
                "total_entries": row["total_entries"] or 0,
                "avg_percent_used": row["avg_percent_used"] or 0.0,
                "max_percent_used": row["max_percent_used"] or 0.0,
                "min_percent_used": row["min_percent_used"] or 0.0,
                "avg_total_bytes": row["avg_total_bytes"] or 0,
                "avg_free_bytes": row["avg_free_bytes"] or 0,
                "avg_used_bytes": row["avg_used_bytes"] or 0,
            }
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def clear_old(self, days: int = 90) -> int:
        """
        Clear trend entries older than specified days.

        Args:
            days: Keep entries newer than this.

        Returns:
            int: Number of entries deleted.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            with self.db.transaction():
                cursor = self.db.execute(
                    """
                    DELETE FROM disk_trend
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                    """,
                    (days,),
                )
            count = cursor.rowcount
            logger.info(f"Cleared {count} old disk trend entries")
            return count
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e


__all__ = ["DiskTrendEntry", "TrendRepository"]
