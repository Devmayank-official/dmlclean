"""
Plain Text Formatter for DMLClean.

Outputs data in simple plain text format for scripts and cron jobs.
"""

from __future__ import annotations

from typing import Any

from dmlclean.cli.formatters.base import Formatter
from dmlclean.utils.sizes import humanize_size


class PlainFormatter(Formatter):
    """
    Plain text output formatter.

    Formats data as simple text for scripts, cron jobs, and minimal output.

    Usage:
        ```python
        formatter = PlainFormatter()
        output = formatter.format(scan_result)
        print(output)  # Plain text
        ```
    """

    def __init__(self, separator: str = ", ") -> None:
        """
        Initialize plain text formatter.

        Args:
            separator: Separator for list items (default: ", ").
        """
        self.separator = separator

    def format(self, data: Any) -> str:
        """
        Format data as plain text.

        Args:
            data: Data to format (scan result, clean result, etc.).

        Returns:
            str: Plain text output.
        """
        if data is None:
            return ""

        # Handle dict data
        if isinstance(data, dict):
            return self._format_dict(data)

        # Handle objects with to_dict() method
        if hasattr(data, "to_dict"):
            return self._format_dict(data.to_dict())

        # Handle list
        if isinstance(data, list):
            return self.separator.join(str(item) for item in data)

        # Fallback: convert to string
        return str(data)

    def _format_dict(self, data: dict[str, Any]) -> str:
        """
        Format dictionary as plain text.

        Args:
            data: Dictionary to format.

        Returns:
            str: Formatted text.
        """
        lines = []

        # Extract common fields
        total_files = data.get("total_files", 0)
        total_size = data.get("total_size_bytes", 0)
        total_size_human = humanize_size(total_size)

        # Format based on data type
        if "candidates" in data:
            # Scan result
            lines.append(f"{total_files} files, {total_size_human}")
        elif "files_deleted" in data:
            # Clean result
            files_deleted = data.get("files_deleted", 0)
            lines.append(f"Deleted: {files_deleted} files ({total_size_human})")
        elif "id" in data and "timestamp" in data:
            # History entry
            lines.append(f"{data['id'][:8]} | {data['timestamp'][:19]} | {data.get('mode', 'N/A')}")
        else:
            # Generic key-value pairs
            for key, value in data.items():
                if key.endswith("_bytes") and isinstance(value, int):
                    lines.append(f"{key}: {humanize_size(value)}")
                else:
                    lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def get_format_name(self) -> str:
        """Get format name."""
        return "plain"


__all__ = ["PlainFormatter"]
