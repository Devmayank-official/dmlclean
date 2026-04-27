"""
Storage-related exceptions for DMLClean.

These exceptions are raised when database operations, migrations,
or repository operations fail.
"""

from __future__ import annotations

from dmlclean.exceptions.base import DMLCleanError


class DatabaseError(DMLCleanError):
    """
    Base exception for database errors.

    Raised when there is an issue with SQLite database operations.

    Exit code: 1
    """

    def __init__(self, message: str) -> None:
        """
        Initialize a DatabaseError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, exit_code=1)


class DatabaseConnectionError(DatabaseError):
    """
    Exception raised when database connection fails.

    Exit code: 1
    """

    def __init__(self, db_path: str, reason: str | None = None) -> None:
        """
        Initialize a DatabaseConnectionError.

        Args:
            db_path: Path to the database file.
            reason: Optional reason for connection failure.
        """
        message = f"Failed to connect to database: {db_path}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)
        self.db_path = db_path
        self.reason = reason


class MigrationError(DatabaseError):
    """
    Exception raised when database migration fails.

    This occurs when a migration SQL file cannot be applied,
    or when the schema is incompatible.

    Exit code: 1

    Example:
        ```python
        try:
            db.run_migrations()
        except sqlite3.Error as e:
            raise MigrationError(f"Migration {version} failed: {e}")
        ```
    """

    def __init__(self, message: str, version: str | None = None) -> None:
        """
        Initialize a MigrationError.

        Args:
            message: Human-readable error message.
            version: Optional migration version that failed.
        """
        super().__init__(message)
        self.version = version


class MigrationNotFoundError(MigrationError):
    """
    Exception raised when a requested migration file is not found.

    Exit code: 1
    """

    def __init__(self, version: str) -> None:
        """
        Initialize a MigrationNotFoundError.

        Args:
            version: The migration version that was not found.
        """
        super().__init__(f"Migration not found: {version}", version=version)
        self.version = version


class RepositoryError(DMLCleanError):
    """
    Base exception for repository operation errors.

    Raised when CRUD operations on repositories fail.

    Exit code: 1
    """

    def __init__(self, message: str, entity_type: str | None = None) -> None:
        """
        Initialize a RepositoryError.

        Args:
            message: Human-readable error message.
            entity_type: Optional type of entity (e.g., 'history', 'schedule').
        """
        super().__init__(message, exit_code=1)
        self.entity_type = entity_type


class EntityNotFoundError(RepositoryError):
    """
    Exception raised when a requested entity is not found in repository.

    Exit code: 1
    """

    def __init__(self, entity_type: str, entity_id: str) -> None:
        """
        Initialize an EntityNotFoundError.

        Args:
            entity_type: Type of entity (e.g., 'history', 'schedule').
            entity_id: The entity ID that was not found.
        """
        super().__init__(
            f"{entity_type} not found: {entity_id}",
            entity_type=entity_type,
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
