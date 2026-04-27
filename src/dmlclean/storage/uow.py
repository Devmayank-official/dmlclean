# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Unit of Work Pattern for DMLClean.

The Unit of Work pattern maintains a list of objects affected by a business
transaction and coordinates the writing out of changes and the resolution of
concurrency problems.

This implementation provides:
- Atomic multi-repository operations
- Transaction boundary management
- Automatic rollback on failure
- Repository access within transaction

Example:
    ```python
    from dmlclean.storage.uow import UnitOfWork
    from dmlclean.storage.database import Database

    db = Database()
    db.connect()

    # Use Unit of Work for atomic operations
    with UnitOfWork(db).commit() as uow:
        # All repositories available
        uow.history.create(entry)
        uow.manifest.create(manifest)
        uow.trend.record(trend_point)
        # All changes committed atomically on exit
    ```
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from loguru import logger

from dmlclean.storage.database import Database
from dmlclean.storage.history_repo import HistoryRepository
from dmlclean.storage.manifest_repo import ManifestRepository
from dmlclean.storage.protected_repo import ProtectedRepository
from dmlclean.storage.schedule_repo import ScheduleRepository
from dmlclean.storage.trend_repo import TrendRepository


class UnitOfWork:
    """
    Unit of Work for atomic multi-repository operations.

    The Unit of Work pattern ensures that operations across multiple
    repositories are treated as a single atomic transaction. Either all
    operations succeed, or all are rolled back.

    This class provides:
    - Access to all repositories within a transaction
    - Automatic commit on successful exit
    - Automatic rollback on exception
    - Clear transaction boundaries

    Attributes:
        db: Database instance managing the transaction.
        history: History repository.
        manifest: Manifest repository.
        protected: Protected repository.
        schedule: Schedule repository.
        trend: Trend repository.

    Example:
        ```python
        # Basic usage
        with UnitOfWork(db).commit() as uow:
            uow.history.create(entry)
            uow.manifest.create(manifest)
            # Both operations commit atomically

        # With error handling
        try:
            with UnitOfWork(db).commit() as uow:
                uow.schedule.create(job)
                uow.history.create(log_entry)
                # If either fails, both are rolled back
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            # Automatic rollback occurred
        ```
    """

    def __init__(self, db: Database) -> None:
        """
        Initialize the Unit of Work.

        Args:
            db: Database instance managing transactions.
        """
        self.db = db

        # Initialize all repositories
        # These share the same database connection, ensuring transaction isolation
        self.history = HistoryRepository(db)
        self.manifest = ManifestRepository(db)
        self.protected = ProtectedRepository(db)
        self.schedule = ScheduleRepository(db)
        self.trend = TrendRepository(db)

        logger.debug("UnitOfWork initialized")

    @contextmanager
    def commit(self) -> Generator[UnitOfWork, None, None]:
        """
        Context manager for atomic transaction commit.

        This context manager wraps all operations in a database transaction.
        Changes are committed on successful exit, or rolled back on exception.

        Usage:
            ```python
            with UnitOfWork(db).commit() as uow:
                # All repositories available
                uow.history.create(entry)
                uow.manifest.create(manifest)

                # On successful exit:
                # - All changes are committed atomically
                # - Transaction is closed

                # If exception occurs:
                # - All changes are rolled back
                # - Transaction is closed
            ```

        Yields:
            UnitOfWork: Self-reference for repository access.

        Raises:
            DatabaseError: If commit fails (will rollback automatically).
        """
        logger.debug("UnitOfWork: Starting transaction")

        try:
            # Yield self for repository access
            yield self

            # Commit transaction
            self.db._connection.commit()
            logger.debug("UnitOfWork: Transaction committed")

        except Exception as e:
            # Rollback on any exception
            self.db._connection.rollback()
            logger.error(f"UnitOfWork: Transaction rolled back: {e}")
            raise

        finally:
            logger.debug("UnitOfWork: Transaction closed")

    @contextmanager
    def transaction(self) -> Generator[UnitOfWork, None, None]:
        """
        Alias for commit() context manager.

        This provides an alternative name for the commit() context manager,
        allowing more explicit transaction semantics.

        Usage:
            ```python
            with UnitOfWork(db).transaction() as uow:
                uow.history.create(entry)
                # Changes committed on exit
            ```

        Yields:
            UnitOfWork: Self-reference for repository access.
        """
        with self.commit() as uow:
            yield uow

    def __enter__(self) -> UnitOfWork:
        """
        Enter context without automatic commit.

        Use this when you want manual control over commit/rollback.

        Returns:
            UnitOfWork: Self-reference.

        Example:
            ```python
            with UnitOfWork(db) as uow:
                uow.history.create(entry)
                # Must manually commit
                uow.db._connection.commit()
            ```
        """
        logger.debug("UnitOfWork: Context entered (manual commit)")
        return self

    def __exit__(
        self, exc_type: type[Exception] | None, exc_val: Exception | None, exc_tb: object | None
    ) -> None:
        """
        Exit context, closing the transaction.

        If an exception occurred, the transaction is rolled back.
        Otherwise, it remains open for manual commit.

        Args:
            exc_type: Exception type if raised.
            exc_val: Exception value if raised.
            exc_tb: Exception traceback if raised.
        """
        if exc_val is not None:
            # Exception occurred, rollback
            self.db._connection.rollback()
            logger.error(f"UnitOfWork: Rolled back due to exception: {exc_val}")
        else:
            logger.debug("UnitOfWork: Context exited (no automatic commit)")


__all__ = ["UnitOfWork"]
