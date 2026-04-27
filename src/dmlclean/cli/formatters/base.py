"""
Abstract base class for Formatters.

All formatters must inherit from this class and implement
the format() method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Formatter(ABC):
    """
    Abstract base class for output formatters.

    The Formatter strategy pattern allows pluggable output formats
    for CLI commands (table, JSON, plain text, etc.).

    Example:
        ```python
        class JsonFormatter(Formatter):
            def format(self, data: Any) -> str:
                return json.dumps(data, indent=2)
        ```
    """

    @abstractmethod
    def format(self, data: Any) -> str:
        """
        Format data for output.

        Args:
            data: Data to format (scan result, clean result, etc.).

        Returns:
            str: Formatted output string.
        """
        pass

    def can_format(self, data_type: type) -> bool:
        """
        Check if this formatter can handle a specific data type.

        Args:
            data_type: Type of data to check.

        Returns:
            bool: True if formatter can handle this type.
        """
        # Default: all formatters can handle any type
        # Subclasses can override for type-specific validation
        return True

    def get_format_name(self) -> str:
        """
        Get the format name.

        Returns:
            str: Format name (e.g., 'json', 'table', 'plain').
        """
        return self.__class__.__name__.lower().replace("formatter", "")


__all__ = ["Formatter"]
