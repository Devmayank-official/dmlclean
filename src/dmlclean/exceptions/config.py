"""
Configuration-related exceptions for DMLClean.
"""

from __future__ import annotations

from dmlclean.exceptions.base import DMLCleanError


class ConfigError(DMLCleanError):
    """
    Base exception for configuration errors.

    Raised when there is an issue with loading, parsing, or validating
    the configuration file.

    Exit code: 1
    """

    def __init__(self, message: str) -> None:
        """
        Initialize a ConfigError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, exit_code=1)


class SchemaValidationError(ConfigError):
    """
    Exception raised when configuration schema validation fails.

    This occurs when the TOML config file contains invalid values
    that fail Pydantic schema validation.

    Exit code: 1

    Example:
        ```python
        try:
            config = ConfigSchema(**raw_config)
        except ValidationError as e:
            raise SchemaValidationError(f"Invalid config: {e}")
        ```
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        """
        Initialize a SchemaValidationError.

        Args:
            message: Human-readable error message.
            field: Optional field name that failed validation.
        """
        super().__init__(message)
        self.field = field


class ConfigKeyNotFoundError(ConfigError):
    """
    Exception raised when a requested config key is not found.

    This occurs when using `dmlclean config get <key>` with an
    invalid or non-existent key.

    Exit code: 1

    Example:
        ```python
        if key not in config:
            raise ConfigKeyNotFoundError(f"Config key not found: {key}")
        ```
    """

    def __init__(self, key: str) -> None:
        """
        Initialize a ConfigKeyNotFoundError.

        Args:
            key: The config key that was not found.
        """
        super().__init__(f"Config key not found: {key}")
        self.key = key
