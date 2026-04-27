"""
Table Formatter for DMLClean.

Outputs data as Rich-formatted tables.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dmlclean.cli.formatters.base import Formatter
from dmlclean.utils.sizes import humanize_size


class TableFormatter(Formatter):
    """
    Rich table output formatter.

    Formats data as Rich tables with colors, borders, and formatting.

    Usage:
        ```python
        formatter = TableFormatter(console)
        output = formatter.format(scan_result)
        console.print(output)  # Rich renderable
        ```
    """

    def __init__(self, console: Console | None = None) -> None:
        """
        Initialize table formatter.

        Args:
            console: Rich console (creates default if None).
        """
        self.console = console or Console()

    def format(self, data: Any) -> str:
        """
        Format data as Rich table.

        Note: This formatter renders directly to console.
        Returns empty string as output is via Rich renderables.

        Args:
            data: Data to format (scan result, clean result, etc.).

        Returns:
            str: Empty string (output is via Rich console).
        """
        # Route to appropriate render method
        if self._is_scan_result(data):
            self._render_scan_result(data)
        elif self._is_clean_result(data):
            self._render_clean_result(data)
        elif self._is_history_list(data):
            self._render_history_table(data)
        elif isinstance(data, dict):
            self._render_dict_table(data)
        else:
            self.console.print(str(data))

        return ""  # Rich renders directly

    def _is_scan_result(self, data: Any) -> bool:
        """Check if data is a scan result."""
        return (
            hasattr(data, "stats") and hasattr(data, "paths") and hasattr(data.stats, "total_files")
        )

    def _is_clean_result(self, data: Any) -> bool:
        """Check if data is a clean result."""
        return hasattr(data, "stats") and hasattr(data.stats, "deleted")

    def _is_history_list(self, data: Any) -> bool:
        """Check if data is a list of history entries."""
        return isinstance(data, list) and len(data) > 0 and hasattr(data[0], "timestamp")

    def _render_scan_result(self, data: Any) -> None:
        """Render scan result."""
        stats = data.stats

        # Header
        self.console.print("\n[bold green]✓ Scan Complete[/bold green]")
        self.console.print(
            f"Files: {stats.total_files} | Size: {humanize_size(stats.total_size_bytes)}"
        )

        # By category if available
        if hasattr(data, "by_category") and data.by_category:
            self.console.print("\n[bold]By Category:[/bold]")

            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Category", style="cyan")
            table.add_column("Files", justify="right")
            table.add_column("Size", justify="right")

            for category, items in sorted(
                data.by_category.items(),
                key=lambda x: sum(c.size_bytes for c in x[1]),
                reverse=True,
            ):
                total_size = sum(c.size_bytes for c in items)
                table.add_row(
                    category.value if hasattr(category, "value") else str(category),
                    str(len(items)),
                    humanize_size(total_size),
                )

            self.console.print(table)

    def _render_clean_result(self, data: Any) -> None:
        """Render clean result."""
        stats = data.stats

        self.console.print("\n[bold green]✓ Clean Complete[/bold green]")

        table = Table(show_header=False, box=None)
        table.add_column("Label", style="cyan")
        table.add_column("Value")

        table.add_row("Files deleted:", str(stats.deleted))
        table.add_row("Files failed:", str(stats.failed))
        table.add_row("Files skipped:", str(stats.skipped))
        table.add_row("Total size:", humanize_size(stats.total_size_bytes))
        table.add_row("Success rate:", stats.success_rate)

        self.console.print(table)

    def _render_history_table(self, entries: list[Any]) -> None:
        """Render history entries."""
        if not entries:
            self.console.print("[yellow]No cleaning history.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp")
        table.add_column("Mode")
        table.add_column("Files")
        table.add_column("Size")
        table.add_column("Status")

        for entry in entries[:20]:  # Limit to 20 entries
            if hasattr(entry, "to_dict"):
                d = entry.to_dict()
            else:
                d = entry

            table.add_row(
                d.get("id", "N/A")[:8],
                d.get("timestamp", "N/A")[:19].replace("T", " "),
                d.get("mode", "N/A"),
                str(d.get("files_deleted", 0)),
                humanize_size(d.get("size_bytes", 0)),
                f"[{'green' if d.get('status') == 'complete' else 'red'}]{d.get('status', 'N/A')}[/{'green' if d.get('status') == 'complete' else 'red'}]",
            )

        self.console.print(table)

        if len(entries) > 20:
            self.console.print(f"[dim]... and {len(entries) - 20} more entries[/dim]")

    def _render_dict_table(self, data: dict[str, Any]) -> None:
        """Render generic dict as table."""
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for key, value in data.items():
            if isinstance(value, dict):
                # Nested dict - skip or summarize
                table.add_row(key, f"[dim]{len(value)} items[/dim]")
            elif isinstance(value, list):
                table.add_row(key, f"[dim]{len(value)} items[/dim]")
            elif key.endswith("_bytes") and isinstance(value, int):
                table.add_row(key, humanize_size(value))
            else:
                table.add_row(key, str(value))

        self.console.print(table)

    def render_panel(self, content: str, title: str = "", style: str = "blue") -> None:
        """
        Render content in a panel.

        Args:
            content: Content to display.
            title: Panel title.
            style: Border color style.
        """
        self.console.print(
            Panel(
                content,
                title=f"[bold {style}]{title}[/bold {style}]",
                border_style=style,
            )
        )

    def get_format_name(self) -> str:
        """Get format name."""
        return "table"


__all__ = ["TableFormatter"]
