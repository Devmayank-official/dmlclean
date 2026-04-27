"""
Protect command for DMLClean.

Manages the Protected Zone.
Uses ProtectRequest/ProtectionEntry DTOs for type-safe operations.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

import typer
from rich.table import Table

from dmlclean.cli.app import console
from dmlclean.container import get_container
from dmlclean.dtos.protect import ProtectRequest

app = typer.Typer(help="Manage Protected Zone.")


def _get_service() -> ProtectionService:
    """Get ProtectionService instance from container."""
    container = get_container()
    return container.protection_service


@app.command("add")
def protect_add(
    path: str = typer.Argument(..., help="Path or glob pattern to protect."),
    description: str = typer.Option("", "--description", "-d", help="Description."),
    glob: bool = typer.Option(False, "--glob", "-g", help="Treat as glob pattern."),
) -> None:
    """Add a path to the Protected Zone.

    Examples:
        # Add exact path
        dmlclean protect add "~/My Project" -d "Important files"

        # Add glob pattern
        dmlclean protect add "**/*.log" -d "All log files" --glob
    """
    service = _get_service()

    try:
        # Create request DTO (v2 pattern)
        request = ProtectRequest(path=path, description=description, is_glob=glob)

        entry = service.add_protection(
            path=request.path,
            description=description,
            is_glob=glob,
        )
        console.print(f"[green]✓ Added to Protected Zone:[/green] {path}")
        console.print(f"  ID: {entry.id[:8]}")
        console.print(f"  Type: {'Glob' if glob else 'Path'}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("remove")
def protect_remove(
    path_or_id: str = typer.Option(..., "--path", "-p", help="Path or ID to remove."),
) -> None:
    """Remove a path from the Protected Zone.

    Examples:
        # Remove by ID
        dmlclean protect remove -p abc123

        # Remove by path
        dmlclean protect remove -p "C:\\My Project"
    """
    service = _get_service()

    # Try to find by ID first
    entry = service.get_protection(path_or_id)
    if entry:
        if service.remove_protection(entry.id):
            console.print(f"[green]✓ Removed from Protected Zone:[/green] {entry.path}")
            return

    # Try to find by path
    entry = service.get_protection_by_path(path_or_id)
    if entry:
        if service.remove_protection(entry.id):
            console.print(f"[green]✓ Removed from Protected Zone:[/green] {entry.path}")
            return

    console.print(f"[yellow]Not found in Protected Zone:[/yellow] {path_or_id}")


@app.command("list")
def protect_list(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """List all protected paths."""
    import sys

    service = _get_service()
    entries = service.list_protected()

    if not entries:
        console.print("[yellow]No protected paths configured.[/yellow]")
        sys.exit(0)

    if json_output:
        import json

        print(
            json.dumps(
                [e.to_dict() if hasattr(e, "to_dict") else str(e) for e in entries], indent=2
            )
        )
        sys.exit(0)

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Path/Pattern")
    table.add_column("Description")

    for entry in entries:
        entry_type = "Glob" if entry.is_glob else "Path"
        table.add_row(
            entry.id[:8],
            entry_type,
            entry.path,
            entry.description or "-",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(entries)} protected paths[/dim]")
    sys.exit(0)


@app.command("check")
def protect_check(
    path: str = typer.Option(..., "--path", "-p", help="Path to check."),
) -> None:
    """Check if a path is protected.

    Examples:
        dmlclean protect check -p "C:\\My Project"
    """
    import sys

    service = _get_service()
    result = service.check_protection(path)

    if result.is_protected:
        console.print(f"[green]✓ PROTECTED[/green]: {path}")
        console.print(f"  Reason: {result.reason}")
    else:
        console.print(f"[yellow]○ NOT PROTECTED[/yellow]: {path}")

    sys.exit(0)
