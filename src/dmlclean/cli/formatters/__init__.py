"""
Formatter Strategy Pattern for DMLClean.

Abstract base class and concrete implementations for:
- Table formatting (Rich)
- JSON formatting
- Plain text formatting

Usage:
    ```python
    from dmlclean.cli.formatters import get_formatter

    # Get formatter based on output type
    formatter = get_formatter("json")
    output = formatter.format(scan_result)

    # Or use factory directly
    from dmlclean.cli.formatters.factory import FormatterFactory
    formatter = FormatterFactory.create("table")
    ```
"""

from dmlclean.cli.formatters.base import Formatter
from dmlclean.cli.formatters.json_fmt import JsonFormatter
from dmlclean.cli.formatters.plain import PlainFormatter
from dmlclean.cli.formatters.table import TableFormatter

__all__ = [
    "Formatter",
    "FormatterFactory",
    "JsonFormatter",
    "PlainFormatter",
    "TableFormatter",
    "get_formatter",
]
