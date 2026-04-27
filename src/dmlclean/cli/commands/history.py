"""
History command for DMLClean.

Manages cleaning history and undo operations.
Uses HistoryRequest/HistoryEntry DTOs for type-safe operations.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from dmlclean.cli.app import console
from dmlclean.cli.formatters.factory import get_formatter
from dmlclean.container import get_container
from dmlclean.dtos.history import HistoryRequest
from dmlclean.utils.sizes import humanize_size

app = typer.Typer(help="View and manage cleaning history.")


def _get_service():
    """Get HistoryService instance from container."""
    container = get_container()
    return container.history_service


@app.command("list")
def history_list(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum entries to show.",
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Filter by profile.",
    ),
    status: str | None = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by status.",
    ),
    mode: str | None = typer.Option(
        None,
        "--mode",
        "-m",
        help="Filter by mode.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format.",
    ),
) -> None:
    """
    List cleaning history.

    Shows recent cleaning operations with details.
    """
    # Validate limit
    if limit < 1 or limit > 100:
        console.print("[red]Error: --limit must be between 1 and 100.[/red]")
        raise typer.Exit(1)

    try:
        service = _get_service()

        # Create request DTO (v2 pattern)
        request = HistoryRequest(limit=limit, profile=profile, status=status, mode=mode)

        # Get history
        entries = service.list_recent(
            limit=request.limit,
            profile=request.profile,
            status=request.status,
            mode=request.mode,
        )

        if not entries:
            console.print("[yellow]No cleaning history.[/yellow]")
            return

        # Output using formatters
        if json_output:
            formatter = get_formatter("json")
            output = formatter.format(
                {"entries": [e.to_dict() if hasattr(e, "to_dict") else e for e in entries]}
            )
            print(output)
        else:
            _output_terminal(entries)

    except Exception as e:
        console.print(f"[red]Failed: {e}[/red]")
        raise typer.Exit(1)


def _output_terminal(entries: list[Any]) -> None:
    """Output history to terminal."""
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("ID", style="cyan")
    table.add_column("Date/Time")
    table.add_column("Mode")
    table.add_column("Profile")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Status")

    for entry in entries:
        data = entry.to_dict() if hasattr(entry, "to_dict") else entry
        status_color = {
            "complete": "green",
            "partial": "yellow",
            "failed": "red",
            "undone": "blue",
        }.get(data.get("status", ""), "white")

        table.add_row(
            data.get("id", "N/A")[:8],
            data.get("timestamp", "N/A")[:19].replace("T", " "),
            data.get("mode", "N/A"),
            data.get("profile", "N/A"),
            str(data.get("files_deleted", 0)),
            humanize_size(data.get("size_bytes", 0)),
            f"[{status_color}]{data.get('status', 'N/A')}[/{status_color}]",
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(entries)} of most recent operations.[/dim]")


@app.command("show")
def history_show(
    entry_id: str = typer.Argument(..., help="Entry ID to show"),
) -> None:
    """
    Show details of a specific history entry.

    Examples:

        dmlclean history show abc123
    """
    service = _get_service()
    entry = service.get_entry(entry_id)

    if not entry:
        console.print(f"[red]Entry not found:[/red] {entry_id}")
        raise typer.Exit(1)

    data = entry.to_dict() if hasattr(entry, "to_dict") else entry

    console.print(f"[bold]History Entry:[/bold] {data['id'][:8]}")
    console.print(f"[bold]Timestamp:[/bold] {data.get('timestamp', 'N/A')[:19].replace('T', ' ')}")
    console.print(f"[bold]Mode:[/bold] {data.get('mode', 'N/A')}")
    console.print(f"[bold]Profile:[/bold] {data.get('profile', 'N/A')}")
    console.print(f"[bold]Scan Mode:[/bold] {data.get('scan_mode', 'N/A')}")
    console.print(f"[bold]Files Found:[/bold] {data.get('files_found', 0):,}")
    console.print(f"[bold]Files Deleted:[/bold] {data.get('files_deleted', 0):,}")
    console.print(f"[bold]Size Freed:[/bold] {humanize_size(data.get('size_bytes', 0))}")
    console.print(f"[bold]Duration:[/bold] {data.get('duration_ms', 0):,}ms")
    console.print(f"[bold]Status:[/bold] {data.get('status', 'N/A')}")

    if data.get("error_message"):
        console.print(f"[bold red]Error:[/bold red] {data.get('error_message')}")

    if data.get("categories"):
        categories = data.get("categories", [])
        if isinstance(categories, str):
            import json

            try:
                categories = json.loads(categories)
            except Exception:
                categories = []
        if categories:
            console.print(f"[bold]Categories:[/bold] {', '.join(categories)}")


@app.command("undo")
def history_undo(
    entry_id: str = typer.Argument(
        None, help="History entry ID to undo (uses latest if not specified)."
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Restore files from a trash operation."""
    service = _get_service()

    try:
        # Get entry to undo
        if entry_id:
            entry = service.get_entry(entry_id)
            if not entry:
                console.print(f"[red]History entry not found:[/red] {entry_id}")
                raise typer.Exit(1)
        else:
            # Get latest entry
            entries = service.list_recent(limit=1)
            if not entries:
                console.print("[yellow]No operations to undo.[/yellow]")
                raise typer.Exit(0)
            entry = entries[0]

        # Confirm
        if not yes:
            console.print(f"[bold]About to undo:[/bold] {entry.id}")
            console.print(f"  Date: {entry.timestamp[:19].replace('T', ' ')}")
            console.print(f"  Files: {entry.files_deleted}")
            console.print(f"  Size: {humanize_size(entry.size_bytes)}")
            console.print(f"  Mode: {entry.mode}")

            if not typer.confirm("Continue?"):
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

        # Execute undo via UndoManager (service doesn't have undo yet)

        undo_manager = service.undo_manager  # Use the undo manager from service

        manifest = undo_manager.get_manifest(entry.id)
        if manifest is None:
            console.print(f"[red]No manifest found for entry:[/red] {entry.id}")
            raise typer.Exit(1)

        can_undo, reason = undo_manager.can_undo(manifest)
        if not can_undo:
            console.print(f"[red]Cannot undo:[/red] {reason}")
            raise typer.Exit(1)

        result = undo_manager.undo(manifest, dry_run=False)

        total_restored = result.get("total_restored", 0)
        total_failed = result.get("total_failed", 0)

        console.print(f"[green]✓ Restored {total_restored} files[/green]")

        if total_failed > 0:
            console.print(f"[yellow]⚠ Failed to restore {total_failed} files[/yellow]")
            console.print(
                "[dim]Note: send2trash doesn't expose trash location. "
                "Files must be manually restored from OS trash.[/dim]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("clear")
def history_clear() -> None:
    """Clear all cleaning history."""
    if not typer.confirm("Are you sure you want to clear all history? This cannot be undone."):
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(0)

    service = _get_service()
    count = service.clear_history()

    console.print(f"[green]✓ Cleared {count} history entries.[/green]")


@app.command("export")
def history_export(
    output: str = typer.Argument("history.json", help="Output file path."),
) -> None:
    """Export history to JSON."""

    service = _get_service()
    output_path = Path(output)

    count = service.export_history(output_path)

    console.print(f"[green]✓ Exported {count} entries to[/green] {output_path}")
