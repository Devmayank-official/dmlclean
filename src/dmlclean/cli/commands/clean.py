# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Clean command for DMLClean.

Executes cleaning operations with safety checks and confirmation.
Uses CleanRequest/CleanResult DTOs for type-safe operations.
Includes input validation for security.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.panel import Panel

from dmlclean.cli.app import console
from dmlclean.container import get_container
from dmlclean.dtos.clean import CleanProfile, CleanRequest, CleanRequestMode
from dmlclean.utils.sizes import humanize_size
from dmlclean.utils.validators import validate_age_days, validate_file_size, validate_path

app = typer.Typer(help="Execute cleaning operations.")


def _get_service():
    """Get CleaningService instance from container."""
    container = get_container()
    return container.cleaning_service


@app.callback(invoke_without_command=True)
def clean(
    mode: str = typer.Option(
        "dry-run",
        "--mode",
        "-m",
        help="Clean mode: dry-run, trash, or permanent.",
    ),
    profile: str = typer.Option(
        "developer",
        "--profile",
        "-p",
        help="Cleaning profile: developer, designer, system-admin, gamer, minimal.",
    ),
    categories: str | None = typer.Option(
        None,
        "--categories",
        "-c",
        help="Comma-separated list of categories to clean.",
    ),
    min_age: int = typer.Option(
        0,
        "--min-age",
        help="Only clean files older than N days.",
    ),
    min_size: int = typer.Option(
        0,
        "--min-size",
        help="Only clean files larger than N MB.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Required for permanent mode on >threshold files.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompts (dangerous).",
    ),
    paths: list[Path] = typer.Option(
        [],
        "--path",
        help="Paths to clean (uses scan defaults if not specified).",
    ),
) -> None:
    """Execute cleaning operation."""
    if mode not in ("dry-run", "trash", "permanent"):
        console.print(f"[red]Invalid mode: {mode}[/red]")
        sys.exit(1)

    service = _get_service()
    category_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else None

    # Validate paths with security checks
    validated_paths = []
    for p in paths:
        try:
            validated_paths.append(validate_path(p, must_exist=True))
        except Exception as e:
            console.print(f"[red]Invalid path {p}: {e}[/red]")
            sys.exit(1)

    scan_paths = validated_paths if validated_paths else _get_default_paths()

    if not scan_paths:
        console.print("[yellow]No paths to clean.[/yellow]")
        sys.exit(0)

    # Validate numeric parameters
    try:
        min_age = validate_age_days(min_age)
        min_size = validate_file_size(min_size)
    except Exception as e:
        console.print(f"[red]Invalid parameter: {e}[/red]")
        sys.exit(1)

    console.print(f"\n[bold blue]Starting cleaning...[/bold blue] Mode={mode}")

    try:
        # Create DTO for type-safe operation
        request = CleanRequest(
            paths=scan_paths,
            mode=CleanRequestMode(mode),
            profile=CleanProfile(profile),
            categories=category_list,
            min_age_days=min_age,
            min_size_mb=min_size,
        )

        result = service.execute_clean(request)

        files_deleted = result.files_deleted
        size_bytes = result.size_bytes

        if mode == "dry-run":
            console.print(Panel("Dry-run: No files deleted", title="Preview", border_style="blue"))
        else:
            console.print(
                f"[green]✓ Cleaned {files_deleted} files ({humanize_size(size_bytes)})[/green]"
            )

        # Explicit success exit
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Operation failed: {e}[/red]")
        sys.exit(1)


def _get_default_paths() -> list[Path]:
    """Get default paths based on platform."""
    import os

    paths = []
    if sys.platform == "win32":
        paths.append(Path(os.environ.get("TEMP", "C:\\Windows\\Temp")))
    elif sys.platform == "darwin":
        paths.extend([Path.home() / "Library" / "Caches", Path("/tmp")])
    else:
        paths.extend([Path("/tmp"), Path.home() / ".cache"])

    return [p for p in paths if p.exists()]
