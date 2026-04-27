"""
Formatter Factory and utility functions.

Provides factory pattern for creating formatters based on output type.
"""

from __future__ import annotations

from typing import Any

from dmlclean.cli.formatters.base import Formatter
from dmlclean.cli.formatters.json_fmt import JsonFormatter
from dmlclean.cli.formatters.plain import PlainFormatter
from dmlclean.cli.formatters.table import TableFormatter


class FormatterFactory:
    """
    Factory for creating formatters.

    Creates appropriate formatter based on format type or flags.

    Usage:
        ```python
        # Create by format name
        formatter = FormatterFactory.create("json")

        # Create from flags
        formatter = FormatterFactory.from_flags(json_output=True)

        # Create from config
        formatter = FormatterFactory.from_config(config)
        ```
    """

    # Registry of available formatters
    _registry: dict[str, type[Formatter]] = {
        "json": JsonFormatter,
        "table": TableFormatter,
        "plain": PlainFormatter,
        "text": PlainFormatter,
    }

    @classmethod
    def create(cls, format_type: str) -> Formatter:
        """
        Create a formatter by format type.

        Args:
            format_type: Format type ('json', 'table', 'plain').

        Returns:
            Formatter: Formatter instance.

        Raises:
            ValueError: If format type not supported.
        """
        formatter_class = cls._registry.get(format_type.lower())
        if not formatter_class:
            raise ValueError(
                f"Unsupported format type: {format_type}. Supported: {list(cls._registry.keys())}"
            )
        return formatter_class()

    @classmethod
    def from_flags(
        cls,
        json_output: bool = False,
        plain_output: bool = False,
        quiet: bool = False,
    ) -> Formatter:
        """
        Create formatter from CLI flags.

        Args:
            json_output: Output JSON format.
            plain_output: Output plain text.
            quiet: Quiet mode (minimal output).

        Returns:
            Formatter: Appropriate formatter for flags.
        """
        if json_output:
            return cls.create("json")
        elif quiet or plain_output:
            return cls.create("plain")
        else:
            return cls.create("table")

    @classmethod
    def register_formatter(cls, name: str, formatter_class: type[Formatter]) -> None:
        """
        Register a custom formatter.

        Args:
            name: Format name.
            formatter_class: Formatter class.

        Example:
            ```python
            class XmlFormatter(Formatter):
                def format(self, data): ...

            FormatterFactory.register_formatter("xml", XmlFormatter)
            ```
        """
        cls._registry[name.lower()] = formatter_class

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """
        Get list of supported format names.

        Returns:
            list[str]: List of format names.
        """
        return list(cls._registry.keys())


def get_formatter(
    format_type: str | None = None,
    json_output: bool = False,
    plain_output: bool = False,
    quiet: bool = False,
) -> Formatter:
    """
    Get a formatter instance.

    Convenience function for FormatterFactory.

    Args:
        format_type: Explicit format type ('json', 'table', 'plain').
        json_output: Output JSON format.
        plain_output: Output plain text.
        quiet: Quiet mode.

    Returns:
        Formatter: Formatter instance.

    Example:
        ```python
        # By format type
        formatter = get_formatter("json")

        # By flags
        formatter = get_formatter(json_output=True)

        # In CLI command
        @app.command()
        def scan(ctx, json_output: bool = False):
            formatter = get_formatter(json_output=json_output)
            result = service.execute_scan()
            output = formatter.format(result)
            console.print(output)
        ```
    """
    if format_type:
        return FormatterFactory.create(format_type)
    return FormatterFactory.from_flags(
        json_output=json_output,
        plain_output=plain_output,
        quiet=quiet,
    )


def format_output(
    data: Any,
    format_type: str | None = None,
    json_output: bool = False,
    plain_output: bool = False,
    quiet: bool = False,
) -> str:
    """
    Format data using appropriate formatter.

    Convenience function that combines formatter creation and formatting.

    Args:
        data: Data to format.
        format_type: Explicit format type.
        json_output: Output JSON format.
        plain_output: Output plain text.
        quiet: Quiet mode.

    Returns:
        str: Formatted output.

    Example:
        ```python
        output = format_output(result, json_output=True)
        print(output)
        ```
    """
    formatter = get_formatter(
        format_type=format_type,
        json_output=json_output,
        plain_output=plain_output,
        quiet=quiet,
    )
    return formatter.format(data)


__all__ = [
    "FormatterFactory",
    "format_output",
    "get_formatter",
]
