"""
Base exception class for DMLClean.

All custom exceptions inherit from this base class.
"""

from __future__ import annotations


class DMLCleanError(Exception):
    """
    Base exception for all DMLClean errors.

    All custom exceptions in DMLClean inherit from this class.
    It provides a consistent interface for error messages and exit codes.

    Attributes:
        message: Human-readable error message.
        exit_code: Process exit code (default: 1).

    Example:
        ```python
        raise DMLCleanError("Something went wrong", exit_code=1)
        ```
    """

    def __init__(self, message: str, exit_code: int = 1) -> None:
        """
        Initialize a DMLCleanError.

        Args:
            message: Human-readable error message.
            exit_code: Process exit code for CLI (default: 1).

        Raises:
            ValueError: If exit_code is not in valid range (0-255).
        """
        if not 0 <= exit_code <= 255:
            raise ValueError(f"Exit code must be 0-255, got {exit_code}")

        super().__init__(message)
        self.message = message
        self.exit_code = exit_code

    def __str__(self) -> str:
        """Return the error message."""
        return self.message

    def __repr__(self) -> str:
        """Return a repr string for debugging."""
        return f"{self.__class__.__name__}(message={self.message!r}, exit_code={self.exit_code})"


# ============================================================================
# GENERIC EXCEPTIONS (For General Use)
# ============================================================================


class ServiceError(DMLCleanError):
    """
    Base exception for service layer errors.

    All service-level exceptions inherit from this class.
    Use this for business logic errors that don't fit other categories.

    Example:
        ```python
        raise ServiceError("Invalid operation sequence")
        ```
    """

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message, exit_code)
        self.service_name = self.__class__.__name__


class ValidationError(ServiceError):
    """
    Exception for validation errors.

    Raised when input validation fails in service layer.

    Example:
        ```python
        if not path.exists():
            raise ValidationError(f"Path does not exist: {path}")
        ```
    """

    pass


class ConfigurationError(DMLCleanError):
    """
    Exception for configuration errors.

    Raised when configuration is invalid or missing.

    Example:
        ```python
        if not config_file.exists():
            raise ConfigurationError(f"Config file not found: {config_file}")
        ```
    """

    pass


class OperationError(ServiceError):
    """
    Exception for operation execution errors.

    Raised when an operation fails during execution.

    Example:
        ```python
        try:
            clean_files()
        except Exception as e:
            raise OperationError(f"Cleaning failed: {e}")
        ```
    """

    pass


class NotFoundError(ServiceError):
    """
    Generic not found error.

    Raised when a requested entity is not found.

    Attributes:
        message: Error message.
        entity_type: Type of entity not found (e.g., "HistoryEntry").
        entity_id: ID of the missing entity.

    Example:
        ```python
        raise NotFoundError(
            "Entry not found",
            entity_type="HistoryEntry",
            entity_id="abc123"
        )
        ```
    """

    def __init__(
        self,
        message: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(message, exit_code)
        self.entity_type = entity_type
        self.entity_id = entity_id

    def __str__(self) -> str:
        if self.entity_type and self.entity_id:
            return f"{self.entity_type} not found: {self.entity_id}"
        return super().__str__()


class DuplicateError(ServiceError):
    """
    Exception for duplicate entry errors.

    Raised when trying to create a duplicate entry.

    Example:
        ```python
        raise DuplicateError(f"Path already protected: {path}")
        ```
    """

    pass


class PermissionError(ServiceError):
    """
    Exception for permission/authorization errors.

    Raised when user lacks required permissions.

    Example:
        ```python
        if not is_admin():
            raise PermissionError("Admin privileges required")
        ```
    """

    pass
