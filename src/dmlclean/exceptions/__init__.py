"""
Exception hierarchy package for DMLClean.

All custom exceptions inherit from DMLCleanError base class.
"""

from dmlclean.exceptions.base import (
    ConfigurationError,
    DMLCleanError,
    DuplicateError,
    NotFoundError,
    OperationError,
    PermissionError,
    ServiceError,
    ValidationError,
)
from dmlclean.exceptions.cli import (
    CLIError,
    ConfirmationAbortedError,
    InvalidCommandError,
)
from dmlclean.exceptions.config import (
    ConfigError,
    ConfigKeyNotFoundError,
    SchemaValidationError,
)
from dmlclean.exceptions.plugin import (
    PluginError,
    PluginNotFoundError,
)
from dmlclean.exceptions.repository import (
    DataError,
    IntegrityError,
    OptimisticLockError,
    RepositoryError,
)
from dmlclean.exceptions.repository import (
    DuplicateError as RepositoryDuplicateError,
)
from dmlclean.exceptions.repository import (
    NotFoundError as RepositoryNotFoundError,
)
from dmlclean.exceptions.safety import (
    ImmutableProtectionError,
    ManifestError,
    ProtectedZoneError,
    UndoError,
)
from dmlclean.exceptions.storage import (
    DatabaseError,
    MigrationError,
)

__all__ = [
    # CLI
    "CLIError",
    # Config
    "ConfigError",
    "ConfigKeyNotFoundError",
    "ConfigurationError",
    "ConfirmationAbortedError",
    # Base
    "DMLCleanError",
    "DataError",
    # Storage
    "DatabaseError",
    "DuplicateError",
    # Safety
    "ImmutableProtectionError",
    "IntegrityError",
    "InvalidCommandError",
    "ManifestError",
    "MigrationError",
    "NotFoundError",
    "OperationError",
    "OptimisticLockError",
    "PermissionError",
    # Plugin
    "PluginError",
    "PluginNotFoundError",
    "ProtectedZoneError",
    "RepositoryDuplicateError",
    # Repository (with aliases to avoid confusion)
    "RepositoryError",
    "RepositoryNotFoundError",
    "SchemaValidationError",
    # Generic Service Exceptions
    "ServiceError",
    "UndoError",
    "ValidationError",
]
