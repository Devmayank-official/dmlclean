"""
JSON Formatter for DMLClean.

Outputs data in JSON format for machine-readable consumption.
"""

from __future__ import annotations

import json
from typing import Any

from dmlclean.cli.formatters.base import Formatter


class JsonFormatter(Formatter):
    """
    JSON output formatter.

    Formats data as indented JSON for machine-readable output.

    Usage:
        ```python
        formatter = JsonFormatter()
        output = formatter.format(scan_result)
        print(output)  # JSON string
        ```
    """

    def __init__(self, indent: int = 2, sort_keys: bool = False) -> None:
        """
        Initialize JSON formatter.

        Args:
            indent: JSON indentation level (default: 2).
            sort_keys: Sort dictionary keys (default: False).
        """
        self.indent = indent
        self.sort_keys = sort_keys

    def format(self, data: Any) -> str:
        """
        Format data as JSON.

        Args:
            data: Data to format (dict, list, or object with to_dict()).

        Returns:
            str: JSON string.

        Raises:
            TypeError: If data is not JSON-serializable.
        """
        # Convert objects with to_dict() method
        serializable = self._to_serializable(data)

        # Format as JSON
        return json.dumps(
            serializable,
            indent=self.indent,
            sort_keys=self.sort_keys,
            default=str,  # Fallback for non-serializable types
        )

    def _to_serializable(self, obj: Any) -> Any:
        """
        Convert object to JSON-serializable format.

        Args:
            obj: Object to convert.

        Returns:
            Any: JSON-serializable object.
        """
        if obj is None:
            return None

        if isinstance(obj, (str, int, float, bool, list, dict)):
            return obj

        # Handle objects with to_dict() method
        if hasattr(obj, "to_dict"):
            result = obj.to_dict()
            return self._to_serializable(result)

        # Handle objects with __dict__
        if hasattr(obj, "__dict__"):
            return self._to_serializable(obj.__dict__)

        # Handle datetime objects
        if hasattr(obj, "isoformat"):
            return obj.isoformat()

        # Fallback: convert to string
        return str(obj)

    def get_format_name(self) -> str:
        """Get format name."""
        return "json"


__all__ = ["JsonFormatter"]
