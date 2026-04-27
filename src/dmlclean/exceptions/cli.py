"""
CLI-related exceptions for DMLClean.

These exceptions are raised when CLI operations fail.
"""

from __future__ import annotations

from dmlclean.exceptions.base import DMLCleanError


class CLIError(DMLCleanError):
    """
    Base exception for CLI errors.

    Raised when there is an issue with CLI command execution.

    Exit code: 1
    """

    def __init__(self, message: str) -> None:
        """
        Initialize a CLIError.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, exit_code=1)


class InvalidCommandError(CLIError):
    """
    Exception raised when an invalid CLI command is used.

    This occurs when:
    - An unknown command is invoked
    - Invalid command arguments are provided

    Exit code: 1

    Example:
        ```python
        if command not in VALID_COMMANDS:
            raise InvalidCommandError(f"Unknown command: {command}")
        ```
    """

    def __init__(self, command: str) -> None:
        """
        Initialize an InvalidCommandError.

        Args:
            command: The invalid command that was used.
        """
        super().__init__(f"Invalid command: {command}")
        self.command = command


class InvalidModeError(CLIError):
    """
    Exception raised when an invalid mode is specified.

    This occurs when:
    - An invalid scan mode is provided (--mode invalid)
    - An invalid clean mode is provided (--mode invalid)

    Exit code: 1
    """

    def __init__(self, mode_type: str, mode: str, valid_modes: list[str]) -> None:
        """
        Initialize an InvalidModeError.

        Args:
            mode_type: Type of mode ('scan' or 'clean').
            mode: The invalid mode that was provided.
            valid_modes: List of valid mode values.
        """
        super().__init__(
            f"Invalid {mode_type} mode: '{mode}'. Valid modes: {', '.join(valid_modes)}"
        )
        self.mode_type = mode_type
        self.mode = mode
        self.valid_modes = valid_modes


class ConfirmationAbortedError(CLIError):
    """
    Exception raised when user cancels a confirmation prompt.

    This occurs when:
    - User presses Ctrl+C during confirmation
    - User types anything other than the required confirmation text

    Exit code: 5 (User cancelled confirmation)

    Example:
        ```python
        if response != "DELETE":
            raise ConfirmationAbortedError()
        ```
    """

    def __init__(self) -> None:
        """Initialize a ConfirmationAbortedError."""
        super().__init__("Operation aborted by user.")
        self.exit_code = 5


class ConfigFileNotFoundError(CLIError):
    """
    Exception raised when a requested config file is not found.

    Exit code: 1
    """

    def __init__(self, config_path: str) -> None:
        """
        Initialize a ConfigFileNotFoundError.

        Args:
            config_path: Path to the config file that was not found.
        """
        super().__init__(f"Config file not found: {config_path}")
        self.config_path = config_path
