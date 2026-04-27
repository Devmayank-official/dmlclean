# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Report command for DMLClean.

Generate reports and export data in JSON, CSV, and HTML formats.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

from pathlib import Path

import typer

from dmlclean.cli.app import console
from dmlclean.container import get_container

app = typer.Typer(help="Generate reports and export data.")


def _get_service():
    """Get ReportService instance from container."""
    container = get_container()
    return container.report_service


@app.callback(invoke_without_command=True)
def report(
    ctx: typer.Context,
) -> None:
    """
    Generate reports.

    Generate summary reports, export to JSON/CSV/HTML.
    """
    if ctx.invoked_subcommand is None:
        # Default to summary
        _show_summary(30)


def _show_summary(days: int = 30) -> None:
    """Show summary report."""
    import sys

    service = _get_service()
    try:
        report_text = service.get_terminal_report(days=days)
        console.print(report_text)
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Failed to generate report: {e}[/red]")
        sys.exit(1)


@app.command("summary")
def report_summary(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to summarize."),
) -> None:
    """Generate summary report."""
    _show_summary(days)


@app.command("last")
def report_last(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format"),
) -> None:
    """Show last cleaning report."""
    import sys

    service = _get_service()
    try:
        report = service.get_last_report()

        if not report:
            console.print("[yellow]No cleaning history found.[/yellow]")
            sys.exit(0)

        if json_output:
            import json

            print(json.dumps(report.to_dict(), indent=2))
        else:
            console.print("[bold]Last Cleaning Report[/bold]\n")
            console.print(f"Mode: {report.mode}")
            console.print(f"Profile: {report.profile}")
            console.print(f"Files Deleted: {report.files_deleted}")
            console.print(f"Size Freed: {report.size_human}")
            console.print(f"Duration: {report.duration_ms}ms")
            console.print(f"Status: {report.status}")

        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Failed to get report: {e}[/red]")
        sys.exit(1)


@app.command("export")
def report_export(
    format: str = typer.Argument(
        "json",
        help="Export format: json, csv, or html.",
    ),
    output: str = typer.Argument(
        "report",
        help="Output file path (without extension).",
    ),
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Number of days to export.",
    ),
    format_option: str | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: json, csv, html (alias for format argument).",
    ),
) -> None:
    """Export report to file."""
    import sys

    service = _get_service()
    output_path = Path(output)

    # Allow --format option to override positional argument
    if format_option:
        format_lower = format_option.lower()
    else:
        format_lower = format.lower()

    try:
        if format_lower == "json":
            output_path = output_path.with_suffix(".json")
            count = service.export_json(output_path, days=days)
        elif format_lower == "csv":
            output_path = output_path.with_suffix(".csv")
            count = service.export_csv(output_path, days=days)
        elif format_lower == "html":
            output_path = output_path.with_suffix(".html")
            count = service.export_html(output_path, days=days)
        else:
            console.print(f"[red]Invalid format:[/red] {format}")
            console.print("Valid formats: json, csv, html")
            sys.exit(1)

        console.print(f"[green]✓ Exported {count} entries to[/green] {output_path}")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")
        sys.exit(1)
