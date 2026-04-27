"""
Error Handler Middleware for DMLClean.

Provides centralized exception handling with:
- Layered exception translation (Service → CLI)
- Rich error panels with contextual messages
- Proper exit codes
- Debug tracebacks for development
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.traceback import Traceback

from dmlclean.exceptions.base import DMLCleanError
from dmlclean.exceptions.cli import ConfirmationAbortedError, InvalidCommandError
from dmlclean.exceptions.config import ConfigError, ConfigKeyNotFoundError, SchemaValidationError
from dmlclean.exceptions.plugin import PluginError, PluginNotFoundError
from dmlclean.exceptions.repository import (
    DataError,
    DuplicateError,
    NotFoundError,
)
from dmlclean.exceptions.safety import (
    ImmutableProtectionError,
    ManifestError,
    ProtectedZoneError,
    UndoError,
)
from dmlclean.exceptions.storage import DatabaseError, MigrationError

if TYPE_CHECKING:
    pass


class ErrorHandler:
    """
    Centralized error handler for CLI middleware.

    Translates service/domain exceptions into user-friendly CLI errors
    with proper exit codes and Rich formatting.

    Usage:
        ```python
        # Register at app startup
        ErrorHandler.register(console)

        # Or use as context manager
        with ErrorHandler(console):
            # CLI command logic
            pass
        ```
    """

    def __init__(self, console: Console, verbose: bool = False) -> None:
        """
        Initialize error handler.

        Args:
            console: Rich console for output.
            verbose: Enable debug tracebacks (default: False).
        """
        self.console = console
        self.verbose = verbose
        self._installed = False

    @classmethod
    def register(cls, console: Console, verbose: bool = False) -> ErrorHandler:
        """
        Register error handler globally.

        Args:
            console: Rich console for output.
            verbose: Enable debug tracebacks.

        Returns:
            ErrorHandler: Registered handler instance.
        """
        handler = cls(console, verbose)
        handler._install_excepthook()
        return handler

    def _install_excepthook(self) -> None:
        """Install global exception hook for uncaught exceptions."""
        if self._installed:
            return

        old_excepthook = sys.excepthook

        def custom_excepthook(exc_type, exc_value, exc_tb) -> None:
            if issubclass(exc_type, KeyboardInterrupt):
                old_excepthook(exc_type, exc_value, exc_tb)
                return

            self.handle_exception(exc_value)

        sys.excepthook = custom_excepthook
        self._installed = True

    def handle_exception(self, exc: BaseException | None) -> None:
        """
        Handle an exception with appropriate formatting.

        Args:
            exc: Exception to handle.
        """
        if exc is None:
            return

        # Log exception for debugging
        from loguru import logger

        logger.exception(f"Unhandled exception: {exc}")

        # Translate and display
        if isinstance(exc, DMLCleanError):
            self._handle_dmlclean_error(exc)
        else:
            self._handle_unknown_error(exc)

    def _handle_dmlclean_error(self, exc: DMLCleanError) -> None:
        """
        Handle DMLCleanError and subclasses.

        Args:
            exc: DMLCleanError instance.
        """
        # Get user-friendly message
        message = self._get_user_message(exc)

        # Display based on error type
        if isinstance(exc, (ConfirmationAbortedError,)):
            self._show_warning_panel(message)
        elif isinstance(exc, (InvalidCommandError,)):
            self._show_error_panel(message, title="Invalid Command")
        elif isinstance(exc, (ConfigError, SchemaValidationError)):
            self._show_error_panel(message, title="Configuration Error")
        elif isinstance(exc, (PluginError, PluginNotFoundError)):
            self._show_error_panel(message, title="Plugin Error")
        elif isinstance(exc, (ProtectedZoneError, ImmutableProtectionError)):
            self._show_error_panel(message, title="Protected Zone Error", style="red")
        elif isinstance(exc, (UndoError, ManifestError)):
            self._show_error_panel(message, title="Undo Error")
        elif isinstance(exc, (DatabaseError, MigrationError)):
            self._show_error_panel(message, title="Database Error", style="red")
        elif isinstance(exc, (NotFoundError, DuplicateError, DataError)):
            self._show_error_panel(message, title="Data Error")
        else:
            self._show_error_panel(message, title="Error")

        # Exit with proper code
        sys.exit(exc.exit_code)

    def _handle_unknown_error(self, exc: BaseException) -> None:
        """
        Handle unknown exceptions (not DMLCleanError).

        Args:
            exc: Unknown exception.
        """
        from loguru import logger

        # Log full traceback
        logger.exception(f"Unexpected error: {exc}")

        if self.verbose:
            # Show full traceback in verbose mode
            self.console.print(
                Panel(
                    Traceback(show_locals=True, width=100),
                    title="[bold red]Unexpected Error (Verbose Mode)[/bold red]",
                    border_style="red",
                )
            )
        else:
            # Show user-friendly message
            error_type = type(exc).__name__
            message = str(exc) or f"An unexpected {error_type} occurred"

            self._show_error_panel(
                f"{message}\n\n[dim]Run with --verbose for full traceback.[/dim]",
                title=f"Unexpected Error: {error_type}",
                style="red",
            )

        sys.exit(1)

    def _get_user_message(self, exc: DMLCleanError) -> str:
        """
        Get user-friendly message for exception.

        Args:
            exc: DMLCleanError instance.

        Returns:
            str: User-friendly message.
        """
        # Add context based on exception type
        if isinstance(exc, NotFoundError):
            if exc.entity_type:
                return f"[bold]{exc.entity_type}[/bold] not found: [yellow]{exc.entity_id}[/yellow]"
        elif isinstance(exc, DuplicateError):
            return f"Duplicate detected: [yellow]{exc.message}[/yellow]"
        elif isinstance(exc, ProtectedZoneError):
            return f"Operation blocked by Protected Zone:\n[yellow]{exc.message}[/yellow]"
        elif isinstance(exc, ConfigKeyNotFoundError):
            return f"Configuration key not found: [yellow]{exc.key}[/yellow]"
        elif isinstance(exc, PluginNotFoundError):
            return f"Plugin not found: [yellow]{exc.plugin_name}[/yellow]"

        return exc.message

    def _show_error_panel(
        self,
        message: str,
        title: str = "Error",
        style: str = "red",
    ) -> None:
        """
        Show error panel.

        Args:
            message: Error message.
            title: Panel title.
            style: Border color style.
        """
        self.console.print(
            Panel(
                message,
                title=f"[bold {style}]{title}[/bold {style}]",
                border_style=style,
            )
        )

    def _show_warning_panel(self, message: str) -> None:
        """
        Show warning panel.

        Args:
            message: Warning message.
        """
        self.console.print(
            Panel(
                message,
                title="[bold yellow]Warning[/bold yellow]",
                border_style="yellow",
            )
        )

    def __enter__(self) -> ErrorHandler:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - handle exception if raised."""
        if exc_val is not None:
            self.handle_exception(exc_val)
            return True  # Exception handled
        return False


__all__ = ["ErrorHandler"]
