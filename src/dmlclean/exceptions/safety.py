"""
Safety-related exceptions for DMLClean.

These exceptions are raised when protected zone violations occur
or when manifest/undo operations fail.
"""

from __future__ import annotations

from pathlib import Path

from dmlclean.exceptions.base import DMLCleanError


class ProtectedZoneError(DMLCleanError):
    """
    Exception raised when a cleaning operation attempts to touch a protected path.

    This is a CRITICAL safety exception that blocks any operation that would
    delete files in the Protected Zone.

    Exit code: 4 (Protected zone violation blocked)

    Example:
        ```python
        if protected_zone.is_protected(path):
            raise ProtectedZoneError(path)
        ```
    """

    def __init__(self, path: Path, reason: str | None = None) -> None:
        """
        Initialize a ProtectedZoneError.

        Args:
            path: The protected path that was blocked.
            reason: Optional reason for protection.
        """
        message = f"Protected zone violation: {path}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, exit_code=4)
        self.path = path
        self.reason = reason


class ImmutableProtectionError(DMLCleanError):
    """
    Exception raised when user tries to remove an immutable protected path.

    Immutable protections are hardcoded (e.g., DMLClean's own storage,
    system directories) and cannot be removed via `dmlclean protect remove`.

    Exit code: 4

    Example:
        ```python
        if path in IMMUTABLE_PROTECTED_PATHS:
            raise ImmutableProtectionError(path)
        ```
    """

    def __init__(self, path: Path) -> None:
        """
        Initialize an ImmutableProtectionError.

        Args:
            path: The immutable protected path.
        """
        super().__init__(
            f"Cannot remove immutable protection: {path}",
            exit_code=4,
        )
        self.path = path


class ManifestError(DMLCleanError):
    """
    Base exception for manifest-related errors.

    Raised when there is an issue creating, saving, loading, or
    processing deletion manifests.

    Exit code: 1
    """

    def __init__(self, message: str) -> None:
        """
        Initialize a ManifestError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, exit_code=1)


class ManifestNotFoundError(ManifestError):
    """
    Exception raised when a requested manifest is not found.

    Exit code: 1
    """

    def __init__(self, manifest_id: str) -> None:
        """
        Initialize a ManifestNotFoundError.

        Args:
            manifest_id: The manifest ID that was not found.
        """
        super().__init__(f"Manifest not found: {manifest_id}")
        self.manifest_id = manifest_id


class UndoError(DMLCleanError):
    """
    Base exception for undo operation errors.

    Raised when there is an issue restoring files from a trash operation.

    Exit code: 1
    """

    def __init__(self, message: str) -> None:
        """
        Initialize an UndoError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, exit_code=1)


class UndoUnavailableError(UndoError):
    """
    Exception raised when undo is not available for a manifest.

    This occurs when:
    - The manifest was for a permanent deletion (no undo possible)
    - The manifest was for a dry-run (no undo needed)
    - Files are no longer in the trash

    Exit code: 1
    """

    def __init__(self, reason: str) -> None:
        """
        Initialize an UndoUnavailableError.

        Args:
            reason: Reason why undo is unavailable.
        """
        super().__init__(f"Undo unavailable: {reason}")
        self.reason = reason


class UndoPartialError(UndoError):
    """
    Exception raised when undo partially succeeded.

    Some files were restored but others failed.

    Exit code: 3 (Partial clean/restore)

    Attributes:
        restored: List of successfully restored paths.
        failed: List of paths that failed to restore.
    """

    def __init__(
        self,
        message: str,
        restored: list[str],
        failed: list[str],
    ) -> None:
        """
        Initialize an UndoPartialError.

        Args:
            message: Human-readable error message.
            restored: List of successfully restored paths.
            failed: List of paths that failed to restore.
        """
        super().__init__(message)
        self.restored = restored
        self.failed = failed
        self.exit_code = 3  # Partial operation
