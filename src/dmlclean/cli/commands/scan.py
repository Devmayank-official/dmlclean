# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Scan command for DMLClean.

Scans for cleanable files using plugin-based architecture.
Uses ScanRequest/ScanResult DTOs for type-safe operations.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel

from dmlclean.cli.app import console
from dmlclean.cli.formatters.factory import get_formatter
from dmlclean.container import get_container
from dmlclean.dtos.scan import ScanMode, ScanRequest
from dmlclean.utils.sizes import humanize_size

app = typer.Typer(help="Scan for cleanable files.")


def _get_service():
    """Get CleaningService instance from container."""
    container = get_container()
    return container.cleaning_service


@app.callback(invoke_without_command=True)
def scan(
    ctx: typer.Context,
    mode: str = typer.Option("fast", "--mode", "-m", help="Scan mode: fast, deep, or custom."),
    categories: str | None = typer.Option(
        None,
        "--categories",
        "-c",
        help="Comma-separated list of categories to scan.",
    ),
    paths: list[Path] = typer.Option(
        [],
        "--path",
        "-p",
        help="Additional paths to scan (can be repeated).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format (machine-readable).",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress output (cron-friendly).",
    ),
) -> None:
    """Scan for cleanable files."""
    if ctx.invoked_subcommand is None:
        _run_scan(mode, categories, paths, json_output, quiet)


def _run_scan(
    mode: str, categories: str | None, paths: list[Path], json_output: bool, quiet: bool
) -> None:
    """Run the scan operation using DTOs."""
    import sys

    # Get service
    service = _get_service()

    # Parse categories
    category_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else None

    # Get scan paths
    scan_paths = list(paths) if paths else _get_default_paths(mode)

    if not scan_paths:
        console.print("[yellow]No paths to scan.[/yellow]")
        sys.exit(0)

    # Create request DTO (v2 pattern)
    request = ScanRequest(
        paths=scan_paths,
        mode=ScanMode(mode.lower()),
        categories=category_list,
    )

    # Show progress
    if not quiet and not json_output:
        console.print(
            Panel(
                f"Scanning {len(scan_paths)} paths...\n"
                f"Mode: [bold]{mode}[/bold] | "
                f"Categories: [bold]{category_list or 'all'}[/bold]",
                title="[bold blue]🔍 Scan in Progress[/bold blue]",
                border_style="blue",
            )
        )

    # Execute scan via service (DTO-based)
    result = service.execute_scan(request)

    # Output results using formatters
    if json_output:
        formatter = get_formatter("json")
        output = formatter.format(result)
        print(output)
    elif quiet:
        print(f"{result.total_files} files, {result.total_size_human}")
    else:
        _output_terminal(result, mode)

    # Explicit success exit
    sys.exit(0)


def _get_default_paths(mode: str) -> list[Path]:
    """Get default paths to scan based on mode and platform."""
    import os

    paths = []
    if sys.platform == "win32":
        paths.append(Path(os.environ.get("TEMP", "C:\\Windows\\Temp")))
    elif sys.platform == "darwin":
        paths.extend([Path.home() / "Library" / "Caches", Path("/tmp")])
    else:
        paths.extend([Path("/tmp"), Path.home() / ".cache"])

    return [p for p in paths if p.exists()]


def _output_terminal(result: Any, mode: str) -> None:
    """Output scan results to terminal."""
    from dmlclean.dtos.scan import ScanResult as ScanResultDTO

    # Handle both DTO and dict formats
    if isinstance(result, ScanResultDTO):
        total_files = result.total_files
        total_size_bytes = result.total_size_bytes
        by_category = result.by_category or {}
        candidates = result.candidates
    else:
        total_files = result.get("total_files", 0)
        total_size_bytes = result.get("total_size_bytes", 0)
        by_category = result.get("by_category", {}) or {}
        candidates = result.get("candidates", 0)

    console.print("\n[bold green]✓ Scan Complete[/bold green]")
    console.print(f"Mode: {mode} | Files: {total_files} | Size: {humanize_size(total_size_bytes)}")

    if by_category:
        console.print("\n[bold]By Category:[/bold]")
        for cat, data in sorted(
            by_category.items(),
            key=lambda x: (x[1] or {}).get("size_bytes", 0) if x[1] else 0,
            reverse=True,
        ):
            if data and isinstance(data, dict):
                count = data.get("count", 0)
                size = data.get("size_bytes", 0)
                console.print(f"  {cat}: {count} files, {humanize_size(size)}")

    console.print(f"\n[dim]Total: {candidates} candidates, {humanize_size(total_size_bytes)}[/dim]")
    console.print("[dim]Run 'dmlclean clean' to execute cleaning.[/dim]")
