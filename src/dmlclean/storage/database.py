"""
SQLite database connection and migration manager for DMLClean.

Provides:
- Database connection with connection pooling
- Schema migrations with version tracking
- Transaction management
- Thread-safe operations
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from loguru import logger

from dmlclean.storage.paths import get_db_path, get_migrations_dir


class DatabaseError(Exception):
    """Base exception for database errors."""

    pass


class MigrationError(DatabaseError):
    """Exception raised when migration fails."""

    pass


class Database:
    """
    SQLite database manager for DMLClean.

    Handles:
    - Connection management with context managers
    - Schema migrations
    - Transaction control
    - Thread-safe operations

    Attributes:
        db_path: Path to SQLite database file.
        _connection: Current database connection.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """
        Initialize the database manager.

        Args:
            db_path: Path to database file. Uses default if None.
        """
        self.db_path = db_path or get_db_path()
        self._connection: sqlite3.Connection | None = None

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Database initialized: {self.db_path}")

    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection.

        Configures:
        - Row factory for dict-like access
        - Foreign keys enabled
        - WAL mode for better concurrency

        Returns:
            sqlite3.Connection: Database connection.

        Raises:
            DatabaseError: If connection fails.
        """
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                isolation_level=None,  # Autocommit mode
                check_same_thread=False,  # Allow async operations
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")

            self._connection = conn
            logger.info(f"Database connected: {self.db_path}")
            return conn

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}") from e

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("Database connection closed")

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database transactions.

        Usage:
            with db.transaction() as conn:
                conn.execute("INSERT ...")
                # Commits on exit, rolls back on exception

        Yields:
            sqlite3.Connection: Connection within transaction.

        Raises:
            DatabaseError: If transaction fails.
        """
        if not self._connection:
            raise DatabaseError("Database not connected. Call connect() first.")

        conn = self._connection
        try:
            yield conn
            conn.commit()
            logger.debug("Transaction committed")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise

    @contextmanager
    def cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager for database cursor.

        Usage:
            with db.cursor() as cursor:
                cursor.execute("SELECT ...")

        Yields:
            sqlite3.Cursor: Database cursor.

        Raises:
            DatabaseError: If cursor creation fails.
        """
        if not self._connection:
            raise DatabaseError("Database not connected. Call connect() first.")

        try:
            cursor = self._connection.cursor()
            yield cursor
        except Exception as e:
            raise DatabaseError(f"Cursor operation failed: {e}") from e
        finally:
            if "cursor" in locals() and cursor:
                cursor.close()

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> sqlite3.Cursor:
        """
        Execute a SQL query.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            sqlite3.Cursor: Result cursor.

        Raises:
            DatabaseError: If query execution fails.
        """
        if not self._connection:
            raise DatabaseError("Database not connected. Call connect() first.")

        try:
            if params:
                return self._connection.execute(query, params)
            else:
                return self._connection.execute(query)
        except sqlite3.Error as e:
            raise DatabaseError(f"Query execution failed: {e}") from e

    def executemany(
        self,
        query: str,
        params_list: list[tuple[Any, ...] | dict[str, Any]],
    ) -> sqlite3.Cursor:
        """
        Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query string.
            params_list: List of parameter sets.

        Returns:
            sqlite3.Cursor: Result cursor.

        Raises:
            DatabaseError: If query execution fails.
        """
        if not self._connection:
            raise DatabaseError("Database not connected. Call connect() first.")

        try:
            return self._connection.executemany(query, params_list)
        except sqlite3.Error as e:
            raise DatabaseError(f"Batch execution failed: {e}") from e

    def fetchone(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> sqlite3.Row | None:
        """
        Execute query and fetch one result.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            sqlite3.Row | None: Single row or None if no results.
        """
        with self.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result  # type: ignore[no-any-return]

    def fetchall(
        self,
        query: str,
        params: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> list[sqlite3.Row]:
        """
        Execute query and fetch all results.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            list[sqlite3.Row]: List of rows.
        """
        with self.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()

    def run_migrations(self) -> int:
        """
        Run all pending database migrations.

        Creates migrations table if not exists, then executes
        migration files in order (001, 002, 003, ...).

        Returns:
            int: Number of migrations applied.

        Raises:
            MigrationError: If migration fails.
        """
        if not self._connection:
            self.connect()

        # Create migrations tracking table
        self.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Get applied migrations
        applied = {row["version"] for row in self.fetchall("SELECT version FROM schema_migrations")}

        # Find migration files
        migrations_dir = get_migrations_dir()
        logger.debug(f"Migrations directory: {migrations_dir}")
        logger.debug(f"Migrations directory exists: {migrations_dir.exists()}")
        if not migrations_dir.exists():
            logger.info("No migrations directory found")
            return 0

        migration_files = sorted(migrations_dir.glob("*.sql"))
        logger.debug(f"Migration files found: {[str(f) for f in migration_files]}")
        if not migration_files:
            logger.info("No migration files found")
            return 0

        migrations_applied = 0

        for migration_file in migration_files:
            version = migration_file.stem  # e.g., "001_initial"

            if version in applied:
                logger.debug(f"Migration {version} already applied, skipping")
                continue

            logger.info(f"Applying migration {version}...")

            try:
                # Read migration SQL
                sql = migration_file.read_text(encoding="utf-8")

                # Execute migration in transaction
                with self.transaction():
                    # Execute all statements in migration
                    # Split on semicolons, but handle multi-line statements (like triggers)
                    statements = self._split_sql_statements(sql)
                    for statement in statements:
                        statement = statement.strip()
                        if statement:
                            self.execute(statement)

                    # Record migration
                    self.execute(
                        "INSERT INTO schema_migrations (version) VALUES (?)",
                        (version,),
                    )

                migrations_applied += 1
                logger.info(f"Migration {version} applied successfully")

            except Exception as e:
                raise MigrationError(f"Migration {version} failed: {e}") from e

        logger.info(f"Database migrations complete: {migrations_applied} applied")
        return migrations_applied

    def get_migration_version(self) -> str:
        """
        Get the current schema version.

        Returns:
            str: Latest migration version or "none" if no migrations.
        """
        result = self.fetchone(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        )
        return result["version"] if result else "none"

    @staticmethod
    def _split_sql_statements(sql: str) -> list[str]:
        """
        Split SQL into individual statements, handling triggers and BEGIN...END blocks.

        Args:
            sql: SQL text with multiple statements.

        Returns:
            list[str]: List of individual SQL statements.
        """
        statements = []
        current = []
        in_trigger = False
        in_begin = False

        for line in sql.split("\n"):
            line.strip()

            # Check for trigger start
            if "CREATE TRIGGER" in line.upper():
                in_trigger = True

            # Check for BEGIN
            if "BEGIN" in line.upper() and not in_begin:
                in_begin = True

            # Check for END (end of trigger body)
            if "END;" in line.upper() and in_begin:
                in_begin = False
                current.append(line)
                statements.append("\n".join(current))
                current = []
                in_trigger = False
                continue

            # If in trigger or BEGIN block, keep adding lines
            if in_trigger or in_begin:
                current.append(line)
            else:
                # Normal statement - split on semicolon
                if ";" in line:
                    parts = line.split(";")
                    for i, part in enumerate(parts):
                        if part.strip():
                            if i == 0 and current:
                                current.append(part)
                                statements.append("\n".join(current))
                                current = []
                            elif i < len(parts) - 1:
                                statements.append(part.strip())
                            else:
                                current.append(part)
                else:
                    current.append(line)

        # Add any remaining statement
        if current:
            remaining = "\n".join(current).strip()
            if remaining:
                statements.append(remaining)

        return statements

    def __enter__(self) -> Database:
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


# Global database instance
_database_instance: Database | None = None


def get_database(db_path: Path | None = None) -> Database:
    """
    Get or create the global database instance.

    Args:
        db_path: Optional custom database path.

    Returns:
        Database: Global database instance.
    """
    global _database_instance

    if _database_instance is None:
        _database_instance = Database(db_path)
        _database_instance.connect()
        _database_instance.run_migrations()
    elif db_path and _database_instance.db_path != db_path:
        # Different path requested, create new instance
        _database_instance.close()
        _database_instance = Database(db_path)
        _database_instance.connect()
        _database_instance.run_migrations()

    return _database_instance


def close_database() -> None:
    """Close the global database instance."""
    global _database_instance

    if _database_instance:
        _database_instance.close()
        _database_instance = None
        logger.debug("Global database instance closed")
