"""
Schedule repository for DMLClean.

CRUD operations for scheduled cleaning jobs following the Repository Pattern.

Example:
    ```python
    from dmlclean.storage import get_database, ScheduleRepository

    db = get_database()
    repo = ScheduleRepository(db)

    # Create
    job = repo.create(
        id="abc123",
        name="Daily Cleanup",
        cron_expression="0 3 * * *",
        enabled=True,
    )

    # Get
    job = repo.get_by_id("abc123")

    # Update
    repo.update("abc123", enabled=False)

    # Delete
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
class ScheduleEntry:
    """
    A scheduled cleaning job.

    Attributes:
        id: Unique identifier (UUID).
        name: Human-readable job name.
        cron_expression: Cron expression (e.g., "0 3 * * *").
        human_readable: Natural language description.
        enabled: Whether job is active.
        profile: Cleaning profile to use.
        scan_mode: Scan mode (fast, deep, custom).
        clean_mode: Clean mode (dry-run, trash, permanent).
        categories: Categories to clean.
        min_age_days: Minimum file age to clean.
        min_size_mb: Minimum file size to clean.
        last_run: ISO 8601 timestamp of last run.
        next_run: ISO 8601 timestamp of next run.
        run_count: Total successful runs.
        fail_count: Consecutive failures.
        last_error: Last error message.
        created_at: ISO 8601 timestamp.
        updated_at: ISO 8601 timestamp.
    """

    id: str
    name: str
    cron_expression: str
    human_readable: str | None = None
    enabled: bool = True
    profile: str = "developer"
    scan_mode: str = "fast"
    clean_mode: str = "dry-run"
    categories: list[str] = field(default_factory=list)
    min_age_days: int = 0
    min_size_mb: int = 0
    last_run: str | None = None
    next_run: str | None = None
    run_count: int = 0
    fail_count: int = 0
    last_error: str | None = None
    created_at: str = ""
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "cron_expression": self.cron_expression,
            "human_readable": self.human_readable,
            "enabled": self.enabled,
            "profile": self.profile,
            "scan_mode": self.scan_mode,
            "clean_mode": self.clean_mode,
            "categories": self.categories,
            "min_age_days": self.min_age_days,
            "min_size_mb": self.min_size_mb,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
            "fail_count": self.fail_count,
            "last_error": self.last_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> ScheduleEntry:
        """Create ScheduleEntry from database row."""
        categories = json.loads(row["categories"]) if row["categories"] else []
        return cls(
            id=row["id"],
            name=row["name"],
            cron_expression=row["cron_expression"],
            human_readable=row["human_readable"],
            enabled=bool(row["enabled"]),
            profile=row["profile"] or "developer",
            scan_mode=row["scan_mode"] or "fast",
            clean_mode=row["clean_mode"] or "dry-run",
            categories=categories,
            min_age_days=row["min_age_days"] or 0,
            min_size_mb=row["min_size_mb"] or 0,
            last_run=row["last_run"],
            next_run=row["next_run"],
            run_count=row["run_count"] or 0,
            fail_count=row["fail_count"] or 0,
            last_error=row["last_error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class ScheduleRepository(Repository[ScheduleEntry]):
    """
    Repository for scheduled job CRUD operations.

    Implements the Repository Pattern with full CRUD operations,
    filtering, and scheduling-specific methods.

    Attributes:
        db: Database instance.

    Example:
        ```python
        db = get_database()
        repo = ScheduleRepository(db)

        # Create
        job = repo.create(
            id="abc123",
            name="Daily Cleanup",
            cron_expression="0 3 * * *",
        )

        # Get
        job = repo.get_by_id("abc123")

        # Update
        repo.update("abc123", enabled=False)

        # List enabled
        enabled = repo.list_all(enabled=True)

        # Mark run
        repo.mark_run("abc123", success=True)
        ```
    """

    def __init__(self, db: Database) -> None:
        """
        Initialize the schedule repository.

        Args:
            db: Database instance.
        """
        super().__init__(ScheduleEntry)
        self.db = db
        logger.debug("ScheduleRepository initialized")

    def create(
        self,
        id: str,  # noqa: A002
        name: str,
        cron_expression: str,
        human_readable: str | None = None,
        enabled: bool = True,
        profile: str = "developer",
        scan_mode: str = "fast",
        clean_mode: str = "dry-run",
        categories: list[str] | None = None,
        min_age_days: int = 0,
        min_size_mb: int = 0,
    ) -> ScheduleEntry:
        """
        Create a new scheduled job.

        Args:
            id: Unique identifier (UUID).
            name: Human-readable job name.
            cron_expression: Cron expression.
            human_readable: Natural language description.
            enabled: Whether job is active.
            profile: Cleaning profile.
            scan_mode: Scan mode.
            clean_mode: Clean mode.
            categories: Categories to clean.
            min_age_days: Minimum file age.
            min_size_mb: Minimum file size.

        Returns:
            ScheduleEntry: Created entry.

        Raises:
            DuplicateError: If job with ID already exists.
            DataError: If data validation fails.
            IntegrityError: If database integrity constraint violated.
            RepositoryError: If database error occurs.
        """
        # Validate required fields
        if not id:
            raise DataError("Schedule ID cannot be empty", field="id", value=id)
        if not name:
            raise DataError("Schedule name cannot be empty", field="name", value=name)
        if not cron_expression:
            raise DataError(
                "Cron expression cannot be empty", field="cron_expression", value=cron_expression
            )

        # Check for duplicate
        if self.exists(id):
            raise DuplicateError(
                "Schedule already exists",
                entity_type="ScheduleEntry",
                entity_id=id,
            )

        now = datetime.now(UTC).isoformat()
        categories_json = json.dumps(categories or [])

        try:
            with self.db.transaction():
                self.db.execute(
                    """
                    INSERT INTO schedules (
                        id, name, cron_expression, human_readable, enabled,
                        profile, scan_mode, clean_mode, categories,
                        min_age_days, min_size_mb, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        id,
                        name,
                        cron_expression,
                        human_readable,
                        1 if enabled else 0,
                        profile,
                        scan_mode,
                        clean_mode,
                        categories_json,
                        min_age_days,
                        min_size_mb,
                        now,
                    ),
                )
        except sqlite3.IntegrityError as e:
            raise IntegrityError(
                f"Database integrity violation: {e}",
                constraint="schedules_pkey",
            ) from e
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

        logger.info(f"Schedule created: {id} ({name})")

        return ScheduleEntry(
            id=id,
            name=name,
            cron_expression=cron_expression,
            human_readable=human_readable,
            enabled=enabled,
            profile=profile,
            scan_mode=scan_mode,
            clean_mode=clean_mode,
            categories=categories or [],
            min_age_days=min_age_days,
            min_size_mb=min_size_mb,
            created_at=now,
        )

    def get_by_id(self, job_id: str) -> ScheduleEntry | None:
        """
        Get a schedule entry by ID.

        Args:
            job_id: Job identifier.

        Returns:
            ScheduleEntry | None: Entry if found.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT * FROM schedules WHERE id = ?",
                (job_id,),
            )
            return ScheduleEntry.from_row(row) if row else None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        enabled: bool | None = None,
    ) -> list[ScheduleEntry]:
        """
        List schedule entries with optional filters.

        Args:
            limit: Maximum entries to return.
            offset: Offset for pagination.
            enabled: Filter by enabled status.

        Returns:
            list[ScheduleEntry]: List of entries.

        Raises:
            RepositoryError: If database error occurs.
        """
        query = "SELECT * FROM schedules WHERE 1=1"
        params: list[Any] = []

        if enabled is not None:
            query += " AND enabled = ?"
            params.append(1 if enabled else 0)

        query += " ORDER BY next_run ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            rows = self.db.fetchall(query, params)
            return [ScheduleEntry.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def update(
        self,
        job_id: str,
        name: str | None = None,
        cron_expression: str | None = None,
        enabled: bool | None = None,
        profile: str | None = None,
        scan_mode: str | None = None,
        clean_mode: str | None = None,
        categories: list[str] | None = None,
        min_age_days: int | None = None,
        min_size_mb: int | None = None,
        next_run: str | None = None,
    ) -> bool:
        """
        Update a schedule entry.

        Args:
            job_id: Job identifier.
            name: New name.
            cron_expression: New cron expression.
            enabled: New enabled status.
            profile: New profile.
            scan_mode: New scan mode.
            clean_mode: New clean mode.
            categories: New categories.
            min_age_days: New minimum age.
            min_size_mb: New minimum size.
            next_run: Next run timestamp.

        Returns:
            bool: True if updated.

        Raises:
            RepositoryError: If database error occurs.
            DataError: If no valid fields provided.
        """
        # Valid fields that can be updated
        valid_fields = {
            "name",
            "cron_expression",
            "enabled",
            "profile",
            "scan_mode",
            "clean_mode",
            "categories",
            "min_age_days",
            "min_size_mb",
            "next_run",
        }

        # Filter to valid fields
        updates = {
            k: v
            for k, v in {
                "name": name,
                "cron_expression": cron_expression,
                "enabled": enabled,
                "profile": profile,
                "scan_mode": scan_mode,
                "clean_mode": clean_mode,
                "categories": categories,
                "min_age_days": min_age_days,
                "min_size_mb": min_size_mb,
                "next_run": next_run,
            }.items()
            if v is not None
        }

        if not updates:
            raise DataError(
                f"No valid fields to update. Valid fields: {valid_fields}",
                field="kwargs",
                value=list(updates.keys()),
            )

        # Check if entry exists
        if not self.exists(job_id):
            return False

        # Build UPDATE query
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = []
        for key, value in updates.items():
            if key == "categories" and isinstance(value, list):
                values.append(json.dumps(value))
            elif key == "enabled" and isinstance(value, bool):
                values.append(1 if value else 0)
            else:
                values.append(value)

        # Add updated_at
        set_clause += ", updated_at = ?"
        values.append(datetime.now(UTC).isoformat())
        values.append(job_id)

        try:
            with self.db.transaction():
                query = f"UPDATE schedules SET {set_clause} WHERE id = ?"  # noqa: S608
                self.db.execute(query, values)
            logger.info(f"Schedule updated: {job_id}")
            return True
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def delete(self, job_id: str) -> bool:
        """
        Delete a schedule entry.

        Args:
            job_id: Job identifier.

        Returns:
            bool: True if deleted.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            with self.db.transaction():
                cursor = self.db.execute(
                    "DELETE FROM schedules WHERE id = ?",
                    (job_id,),
                )
                deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Schedule deleted: {job_id}")
            return deleted
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def exists(self, job_id: str) -> bool:
        """
        Check if a schedule entry exists.

        Args:
            job_id: Job identifier.

        Returns:
            bool: True if exists.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone(
                "SELECT 1 FROM schedules WHERE id = ?",
                (job_id,),
            )
            return row is not None
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def count(self) -> int:
        """
        Count total schedule entries.

        Returns:
            int: Total count.

        Raises:
            RepositoryError: If database error occurs.
        """
        try:
            row = self.db.fetchone("SELECT COUNT(*) as cnt FROM schedules")
            return row["cnt"] if row else 0
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def mark_run(
        self,
        job_id: str,
        success: bool = True,
        error_message: str | None = None,
    ) -> bool:
        """
        Mark a job as run.

        Args:
            job_id: Job identifier.
            success: Whether run was successful.
            error_message: Error message if failed.

        Returns:
            bool: True if updated.
        """
        now = datetime.now(UTC).isoformat()

        try:
            if success:
                cursor = self.db.execute(
                    """
                    UPDATE schedules
                    SET last_run = ?, run_count = run_count + 1, fail_count = 0, last_error = NULL
                    WHERE id = ?
                    """,
                    (now, job_id),
                )
                updated = cursor.rowcount > 0
            else:
                cursor = self.db.execute(
                    """
                    UPDATE schedules
                    SET last_run = ?, fail_count = fail_count + 1, last_error = ?
                    WHERE id = ?
                    """,
                    (now, error_message, job_id),
                )
                updated = cursor.rowcount > 0

            if updated:
                logger.info(f"Schedule run recorded: {job_id} (success={success})")
            return updated
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def clear_all(self) -> int:
        """
        Clear all schedule entries.

        Returns:
            int: Number of entries deleted.
        """
        try:
            cursor = self.db.execute("DELETE FROM schedules")
            count = cursor.rowcount
            logger.info(f"Cleared {count} schedule entries")
            return count
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    def get_enabled(self) -> list[ScheduleEntry]:
        """
        Get all enabled schedules.

        Returns:
            list[ScheduleEntry]: List of enabled schedules.
        """
        return self.list_all(enabled=True)

    def get_by_profile(self, profile: str) -> list[ScheduleEntry]:
        """
        Get schedules by profile.

        Args:
            profile: Profile name.

        Returns:
            list[ScheduleEntry]: List of schedules.
        """
        try:
            rows = self.db.fetchall(
                "SELECT * FROM schedules WHERE profile = ? ORDER BY next_run ASC",
                (profile,),
            )
            return [ScheduleEntry.from_row(row) for row in rows]
        except sqlite3.Error as e:
            raise RepositoryError(f"Database error: {e}") from e

    # ========================================================================
    # ASYNC METHODS (for async service compatibility)
    # ========================================================================

    async def create_async(self, **kwargs: Any) -> ScheduleEntry:
        """Async wrapper for create()."""
        import asyncio

        return await asyncio.to_thread(self.create, **kwargs)

    async def get_by_id_async(self, job_id: str) -> ScheduleEntry | None:
        """Async wrapper for get_by_id()."""
        import asyncio

        return await asyncio.to_thread(self.get_by_id, job_id)

    async def list_all_async(
        self,
        limit: int = 100,
        offset: int = 0,
        enabled: bool | None = None,
    ) -> list[ScheduleEntry]:
        """Async wrapper for list_all()."""
        import asyncio

        return await asyncio.to_thread(self.list_all, limit, offset, enabled)

    async def update_async(
        self,
        job_id: str,
        **kwargs: Any,
    ) -> bool:
        """Async wrapper for update()."""
        import asyncio

        return await asyncio.to_thread(self.update, job_id, **kwargs)

    async def delete_async(self, job_id: str) -> bool:
        """Async wrapper for delete()."""
        import asyncio

        return await asyncio.to_thread(self.delete, job_id)

    async def record_run_async(
        self,
        job_id: str,
        success: bool,
        error_message: str | None = None,
    ) -> bool:
        """Async wrapper for record_run()."""
        import asyncio

        return await asyncio.to_thread(self.record_run, job_id, success, error_message)
