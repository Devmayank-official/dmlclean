"""
Plugin-related exceptions for DMLClean.

These exceptions are raised when plugin operations fail.
"""

from __future__ import annotations

from dmlclean.exceptions.base import DMLCleanError


class PluginError(DMLCleanError):
    """
    Base exception for plugin errors.

    Raised when there is an issue with plugin loading, discovery,
    or execution.

    Exit code: 1
    """

    def __init__(self, message: str, plugin_name: str | None = None) -> None:
        """
        Initialize a PluginError.

        Args:
            message: Human-readable error message.
            plugin_name: Optional plugin name that caused the error.
        """
        super().__init__(message, exit_code=1)
        self.plugin_name = plugin_name


class PluginNotFoundError(PluginError):
    """
    Exception raised when a requested plugin is not found.

    This occurs when:
    - A plugin name in config doesn't match any registered plugin
    - A plugin fails to load during discovery

    Exit code: 1

    Example:
        ```python
        if plugin_name not in plugins:
            raise PluginNotFoundError(plugin_name)
        ```
    """

    def __init__(self, plugin_name: str) -> None:
        """
        Initialize a PluginNotFoundError.

        Args:
            plugin_name: The plugin name that was not found.
        """
        super().__init__(f"Plugin not found: {plugin_name}", plugin_name=plugin_name)
        self.plugin_name = plugin_name


class PluginLoadError(PluginError):
    """
    Exception raised when a plugin fails to load.

    This occurs when a plugin module has import errors or
    missing dependencies.

    Exit code: 1
    """

    def __init__(self, plugin_name: str, reason: str) -> None:
        """
        Initialize a PluginLoadError.

        Args:
            plugin_name: The plugin name that failed to load.
            reason: Reason for the load failure.
        """
        super().__init__(
            f"Failed to load plugin '{plugin_name}': {reason}",
            plugin_name=plugin_name,
        )
        self.reason = reason


class PluginExecutionError(PluginError):
    """
    Exception raised when a plugin execution fails.

    This occurs when a plugin's scan() method raises an exception.

    Exit code: 1
    """

    def __init__(self, plugin_name: str, reason: str) -> None:
        """
        Initialize a PluginExecutionError.

        Args:
            plugin_name: The plugin name that failed.
            reason: Reason for the execution failure.
        """
        super().__init__(
            f"Plugin '{plugin_name}' execution failed: {reason}",
            plugin_name=plugin_name,
        )
        self.reason = reason
