# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Terminal report generator using Rich.

Provides rich terminal output for:
- Scan results
- Clean results
- History reports
- Statistics dashboards
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dmlclean.utils.sizes import humanize_size

if TYPE_CHECKING:
    from dmlclean.dtos.clean import CleanResult
    from dmlclean.dtos.scan import ScanResult
    from dmlclean.models.history import HistoryEntry


class TerminalReporter:
    """
    Generate rich terminal reports for DMLClean operations.

    This class provides formatted terminal output for:
    - Scan results with category breakdown
    - Clean results with before/after comparison
    - History reports with statistics
    - Progress panels and summaries

    Attributes:
        console: Rich console instance for output.
        width: Maximum width for tables (None = auto).

    Example:
        ```python
        reporter = TerminalReporter()
        reporter.render_scan_result(scan_result)
        reporter.render_clean_result(clean_result)
        ```
    """

    def __init__(self, console: Console | None = None, width: int | None = None) -> None:
        """
        Initialize the terminal reporter.

        Args:
            console: Rich console instance (created if None).
            width: Maximum table width (None = auto-detect).
        """
        self.console = console or Console()
        self.width = width

    def render_scan_result(self, result: ScanResult) -> None:
        """
        Render scan results to terminal.

        Args:
            result: Scan result DTO to render.

        Example:
            ```python
            reporter.render_scan_result(scan_result)
            # Outputs: Rich panel with scan statistics
            #          Table with category breakdown
            ```
        """
        # Header panel
        header = Panel(
            f"Scan Mode: [bold]{result.mode}[/bold]\n"
            f"Paths Scanned: [bold]{result.paths_scanned}[/bold]\n"
            f"Total Files: [bold]{result.total_files}[/bold]\n"
            f"Total Size: [bold green]{result.total_size_human}[/bold green]",
            title="[bold blue]🔍 Scan Results[/bold blue]",
            border_style="blue",
        )
        self.console.print(header)
        self.console.print()

        # Category breakdown table
        if result.by_category:
            self.console.print("[bold]By Category:[/bold]")
            table = Table(
                show_header=True,
                header_style="bold cyan",
                width=self.width,
                expand=True,
            )
            table.add_column("Category", style="cyan", ratio=2)
            table.add_column("Files", justify="right", style="green", ratio=1)
            table.add_column("Size", justify="right", style="yellow", ratio=1)

            # Sort by size (largest first)
            sorted_categories = sorted(
                result.by_category.items(),
                key=lambda x: x[1].get("size_bytes", 0),
                reverse=True,
            )

            for category, data in sorted_categories:
                files_count = data.get("count", 0)
                size_bytes = data.get("size_bytes", 0)
                table.add_row(
                    category,
                    f"{files_count:,}",
                    humanize_size(size_bytes),
                )

            self.console.print(table)
            self.console.print()

        # Risk level breakdown
        if result.by_risk:
            self.console.print("[bold]By Risk Level:[/bold]")
            risk_table = Table(
                show_header=True,
                header_style="bold magenta",
                width=self.width,
                expand=True,
            )
            risk_table.add_column("Risk Level", style="magenta")
            risk_table.add_column("Files", justify="right", style="green")
            risk_table.add_column("Size", justify="right", style="yellow")

            risk_order = ["low", "medium", "high", "blocked"]
            for risk in risk_order:
                if risk in result.by_risk:
                    data = result.by_risk[risk]
                    files_count = data.get("count", 0)
                    size_bytes = data.get("size_bytes", 0)

                    # Color coding for risk levels
                    risk_colors = {
                        "low": "green",
                        "medium": "yellow",
                        "high": "red",
                        "blocked": "bright_red",
                    }
                    risk_emoji = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴",
                        "blocked": "⛔",
                    }

                    risk_text = Text(f"{risk_emoji.get(risk, '')} {risk.upper()}")
                    risk_text.stylize(risk_colors.get(risk, "white"))

                    risk_table.add_row(
                        risk_text,
                        f"{files_count:,}",
                        humanize_size(size_bytes),
                    )

            self.console.print(risk_table)
            self.console.print()

        # Summary
        summary_text = (
            f"\n[dim]Total Candidates: {result.candidates:,} files, "
            f"{result.total_size_human}[/dim]\n"
            f"[dim]Run 'dmlclean clean' to execute cleaning.[/dim]"
        )
        self.console.print(summary_text)

    def render_clean_result(self, result: CleanResult) -> None:
        """
        Render clean results to terminal.

        Args:
            result: Clean result DTO to render.

        Example:
            ```python
            reporter.render_clean_result(clean_result)
            # Outputs: Rich panel with cleaning statistics
            #          Success/failure summary
            ```
        """
        # Determine panel style based on success
        if result.success:
            border_style = "green"
            title_emoji = "✓"
            title_text = "Cleaning Complete"
        else:
            border_style = "yellow"
            title_emoji = "⚠"
            title_text = "Cleaning Completed with Warnings"

        # Main statistics panel
        stats_panel = Panel(
            f"Operation ID: [dim]{result.operation_id}[/dim]\n"
            f"Mode: [bold]{result.mode}[/bold]\n"
            f"Profile: [bold]{result.profile}[/bold]\n"
            f"Files Deleted: [bold green]{result.files_deleted:,}[/bold green]\n"
            f"Files Failed: [bold red]{result.files_failed:,}[/bold red]\n"
            f"Files Skipped: [bold yellow]{result.files_skipped:,}[/bold yellow]\n"
            f"Total Size Freed: [bold green]{humanize_size(result.size_bytes)}[/bold green]\n"
            f"Duration: [bold]{result.duration_ms}ms[/bold]",
            title=f"[bold {border_style}]{title_emoji} {title_text}[/bold {border_style}]",
            border_style=border_style,
        )
        self.console.print(stats_panel)

        # Show errors if any
        if result.errors:
            self.console.print()
            self.console.print("[bold red]⚠ Errors Encountered:[/bold red]")

            for i, error in enumerate(result.errors, 1):
                error_panel = Panel(
                    error,
                    title=f"Error {i}",
                    border_style="red",
                )
                self.console.print(error_panel)

        # Manifest reference
        if result.manifest_id:
            self.console.print()
            self.console.print(
                f"[dim]Manifest ID: {result.manifest_id}[/dim]\n"
                f"[dim]Use 'dmlclean history undo' to restore if needed.[/dim]"
            )

    def render_history(
        self,
        entries: list[HistoryEntry],
        show_stats: bool = True,
    ) -> None:
        """
        Render cleaning history to terminal.

        Args:
            entries: List of history entries to render.
            show_stats: Whether to show summary statistics.

        Example:
            ```python
            reporter.render_history(history_entries)
            # Outputs: Table with history entries
            #          Summary statistics (if enabled)
            ```
        """
        if not entries:
            info_panel = Panel(
                "No cleaning history found.\n"
                "Run 'dmlclean clean' to perform your first cleaning operation.",
                title="[bold blue]ℹ History[/bold blue]",
                border_style="blue",
            )
            self.console.print(info_panel)
            return

        # History table
        table = Table(
            show_header=True,
            header_style="bold cyan",
            width=self.width,
            expand=True,
            title="[bold]Cleaning History[/bold]",
            title_style="bold cyan",
        )

        table.add_column("ID", style="dim", max_width=8)
        table.add_column("Date", style="cyan")
        table.add_column("Mode", style="green")
        table.add_column("Profile", style="magenta")
        table.add_column("Files", justify="right", style="yellow")
        table.add_column("Size", justify="right", style="blue")
        table.add_column("Status", justify="center")

        # Sort by timestamp (newest first)
        sorted_entries = sorted(
            entries,
            key=lambda e: e.timestamp,
            reverse=True,
        )

        for entry in sorted_entries[:20]:  # Show last 20 entries
            # Status indicator
            status_emoji = {
                "complete": "✓",
                "partial": "⚠",
                "failed": "✗",
            }
            status_colors = {
                "complete": "green",
                "partial": "yellow",
                "failed": "red",
            }

            status_text = Text(f"{status_emoji.get(entry.status, '?')} {entry.status}")
            status_text.stylize(status_colors.get(entry.status, "white"))

            table.add_row(
                entry.id[:8],  # Short UUID
                entry.timestamp.strftime("%Y-%m-%d %H:%M"),
                entry.mode,
                entry.profile,
                f"{entry.files_deleted:,}",
                humanize_size(entry.size_bytes),
                status_text,
            )

        self.console.print(table)

        # Statistics summary
        if show_stats and len(entries) > 1:
            self.console.print()
            self._render_history_stats(entries)

    def _render_history_stats(self, entries: list[HistoryEntry]) -> None:
        """
        Render summary statistics for history entries.

        Args:
            entries: List of history entries.
        """
        total_files = sum(e.files_deleted for e in entries)
        total_size = sum(e.size_bytes for e in entries)
        successful = sum(1 for e in entries if e.status == "complete")
        failed = sum(1 for e in entries if e.status == "failed")

        stats_panel = Panel(
            f"Total Operations: [bold]{len(entries)}[/bold]\n"
            f"Successful: [bold green]{successful}[/bold green]\n"
            f"Failed: [bold red]{failed}[/bold red]\n"
            f"Total Files Deleted: [bold yellow]{total_files:,}[/bold yellow]\n"
            f"Total Size Freed: [bold green]{humanize_size(total_size)}[/bold green]",
            title="[bold magenta]📊 Summary Statistics[/bold magenta]",
            border_style="magenta",
        )
        self.console.print(stats_panel)

    def render_preview(
        self,
        candidates: list[Any],
        total_size_bytes: int,
    ) -> None:
        """
        Render preview of files to be cleaned.

        Args:
            candidates: List of clean candidates.
            total_size_bytes: Total size in bytes.

        Example:
            ```python
            reporter.render_preview(candidates, total_size)
            # Outputs: Preview panel with file count and size
            ```
        """
        # Group by category
        by_category: dict[str, dict[str, int]] = {}
        for candidate in candidates:
            cat = candidate.category
            if cat not in by_category:
                by_category[cat] = {"count": 0, "size_bytes": 0}
            by_category[cat]["count"] += 1
            by_category[cat]["size_bytes"] += candidate.size_bytes

        # Preview panel
        preview_text = (
            f"Files to Clean: [bold yellow]{len(candidates):,}[/bold yellow]\n"
            f"Total Size: [bold green]{humanize_size(total_size_bytes)}[/bold green]\n\n"
            f"[dim]Categories:[/dim]\n"
        )

        for cat, data in sorted(
            by_category.items(),
            key=lambda x: x[1]["size_bytes"],
            reverse=True,
        )[:5]:  # Show top 5 categories
            preview_text += (
                f"  • {cat}: [bold]{data['count']}[/bold] files, "
                f"[dim]{humanize_size(data['size_bytes'])}[/dim]\n"
            )

        if len(by_category) > 5:
            preview_text += f"  ... and {len(by_category) - 5} more categories\n"

        preview_panel = Panel(
            preview_text,
            title="[bold blue]👁 Preview[/bold blue]",
            border_style="blue",
        )
        self.console.print(preview_panel)

        # Warning for permanent mode
        warning_panel = Panel(
            "[bold yellow]⚠ Warning:[/bold yellow] "
            "Permanent deletion cannot be undone!\n"
            "Make sure to review the files above before proceeding.",
            border_style="yellow",
        )
        self.console.print(warning_panel)

    def print_success(self, message: str, title: str = "Success") -> None:
        """
        Print a success message in a green panel.

        Args:
            message: Success message to display.
            title: Panel title.
        """
        panel = Panel(
            message,
            title=f"[bold green]✓ {title}[/bold green]",
            border_style="green",
        )
        self.console.print(panel)

    def print_error(self, message: str, title: str = "Error") -> None:
        """
        Print an error message in a red panel.

        Args:
            message: Error message to display.
            title: Panel title.
        """
        panel = Panel(
            message,
            title=f"[bold red]✗ {title}[/bold red]",
            border_style="red",
        )
        self.console.print(panel)

    def print_warning(self, message: str, title: str = "Warning") -> None:
        """
        Print a warning message in a yellow panel.

        Args:
            message: Warning message to display.
            title: Panel title.
        """
        panel = Panel(
            message,
            title=f"[bold yellow]⚠ {title}[/bold yellow]",
            border_style="yellow",
        )
        self.console.print(panel)

    def print_info(self, message: str, title: str = "Info") -> None:
        """
        Print an info message in a blue panel.

        Args:
            message: Info message to display.
            title: Panel title.
        """
        panel = Panel(
            message,
            title=f"[bold blue]ℹ {title}[/bold blue]",
            border_style="blue",
        )
        self.console.print(panel)


__all__ = ["TerminalReporter"]
