"""
Storage management command for DMLClean.

Manage DMLClean storage: info, open, clean-temp, migrate, backup, restore, reset.
Cross-platform path resolution with unified storage structure.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table

from dmlclean.cli.app import console
from dmlclean.storage.paths import (
    ensure_all_dirs,
    get_base_dir,
    get_cache_dir,
    get_config_path,
    get_db_path,
    get_manifests_dir,
    get_storage_info,
)

app = typer.Typer(help="Manage DMLClean storage.")


@app.callback(invoke_without_command=True)
def storage(
    ctx: typer.Context,
) -> None:
    """
    Manage DMLClean storage.

    View storage info, clean temp files, backup/restore data.
    """
    if ctx.invoked_subcommand is None:
        _storage_info()


@app.command("info")
def storage_info(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Show storage directory information."""
    _storage_info(json_output)


def _storage_info(json_output: bool = False) -> None:
    """Show storage directory information."""
    info = get_storage_info()

    if json_output:
        print(json.dumps(info, indent=2))
        return

    console.print("[bold blue]DMLClean Storage Information[/bold blue]\n")
    console.print(f"[bold]Base Directory:[/bold] {info['base_dir']}\n")

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Location", style="cyan")
    table.add_column("Path")

    table.add_row("Config", info["config_dir"])
    table.add_row("Data", info["data_dir"])
    table.add_row("History", info["history_dir"])
    table.add_row("Manifests", info["manifests_dir"])
    table.add_row("Reports", info["reports_dir"])
    table.add_row("Logs", info["logs_dir"])
    table.add_row("Cache", info["cache_dir"])

    console.print(table)

    # Show file paths
    console.print("\n[bold]Key Files:[/bold]")
    console.print(f"  Config: {info['config_path']}")
    console.print(f"  Database: {info['db_path']}")
    console.print(f"  Log: {info['log_path']}")
    console.print(f"  State: {info['state_path']}")


@app.command("path")
def storage_path(
    location: str = typer.Argument(
        "base",
        help="Location: base, config, data, history, logs, cache",
    ),
) -> None:
    """
    Show DMLClean storage path for a location.

    Examples:

        dmlclean storage path

        dmlclean storage path config

        dmlclean storage path data
    """
    import sys

    info = get_storage_info()

    location_map = {
        "base": info["base_dir"],
        "config": info["config_dir"],
        "data": info["data_dir"],
        "history": info["history_dir"],
        "logs": info["logs_dir"],
        "cache": info["cache_dir"],
        "manifests": info["manifests_dir"],
        "reports": info["reports_dir"],
        "db": info["db_path"],
        "config_file": info["config_path"],
        "log_file": info["log_path"],
    }

    if location not in location_map:
        console.print(f"[red]Invalid location:[/red] {location}")
        console.print(f"Valid locations: {', '.join(location_map.keys())}")
        raise typer.Exit(1)

    path = location_map[location]
    console.print(f"[bold]{location.title()} Path:[/bold]")
    console.print(path)

    # Show if exists
    from pathlib import Path

    path_obj = Path(path)
    if path_obj.exists():
        console.print("[green]✓ Exists[/green]")
    else:
        console.print("[yellow]○ Does not exist (will be created on first use)[/yellow]")

    # Explicitly exit successfully
    sys.exit(0)


@app.command("open")
def storage_open(
    location: str = typer.Argument(
        "base",
        help="Location to open: base, config, data, history, logs, cache",
    ),
) -> None:
    """
    Open a storage directory in file explorer.

    Examples:

        dmlclean storage open config

        dmlclean storage open logs
    """
    import subprocess
    import sys

    info = get_storage_info()

    location_map = {
        "base": info["base_dir"],
        "config": info["config_dir"],
        "data": info["data_dir"],
        "history": info["history_dir"],
        "logs": info["logs_dir"],
        "cache": info["cache_dir"],
    }

    if location not in location_map:
        console.print(f"[red]Invalid location:[/red] {location}")
        console.print(f"Valid locations: {', '.join(location_map.keys())}")
        raise typer.Exit(1)

    path = Path(location_map[location])

    # Ensure directory exists
    ensure_all_dirs()

    try:
        if sys.platform == "win32":
            subprocess.run(["explorer", str(path)])
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])

        console.print(f"[green]✓ Opened:[/green] {path}")

    except Exception as e:
        console.print(f"[red]Failed to open:[/red] {e}")
        console.print(f"Path: {path}")
        raise typer.Exit(1) from e


@app.command("clean-temp")
def storage_clean_temp(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """
    Clean temporary files from cache.

    Removes files from the temp directory only.
    Does not affect config, data, or history.

    Examples:

        dmlclean storage clean-temp

        dmlclean storage clean-temp --yes
    """
    temp_dir = get_cache_dir() / "temp"

    if not temp_dir.exists():
        console.print("[yellow]Temp directory does not exist.[/yellow]")
        raise typer.Exit(0)

    # Count files
    temp_files = list(temp_dir.glob("*"))
    total_size = sum(f.stat().st_size for f in temp_files if f.is_file())

    if not temp_files:
        console.print("[green]✓ Temp directory is already clean.[/green]")
        raise typer.Exit(0)

    from dmlclean.utils.sizes import humanize_size

    console.print("[bold]Temp files to clean:[/bold]")
    console.print(f"  Files: {len(temp_files)}")
    console.print(f"  Size: {humanize_size(total_size)}")

    if not yes:
        if not typer.confirm("Continue?"):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    # Delete files
    deleted = 0
    for f in temp_files:
        try:
            if f.is_file():
                f.unlink()
                deleted += 1
        except Exception:  # noqa: S110
            pass

    console.print(f"[green]✓ Cleaned {deleted} temp files.[/green]")


@app.command("migrate")
def storage_migrate(
    check: bool = typer.Option(False, "--check", help="Check migrations without applying."),
) -> None:
    """
    Run database migrations.

    Examples:

        dmlclean storage migrate

        dmlclean storage migrate --check
    """
    from dmlclean.storage import get_database

    try:
        db = get_database()

        if check:
            version = db.get_migration_version()
            console.print(f"[bold]Current schema version:[/bold] {version}")
            console.print("[green]✓ Database is up to date.[/green]")
        else:
            count = db.run_migrations()
            if count > 0:
                console.print(f"[green]✓ Applied {count} migration(s).[/green]")
            else:
                console.print("[green]✓ Database is up to date.[/green]")

    except Exception as e:
        console.print(f"[red]Migration failed:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("backup")
def storage_backup(
    output_path: Path = typer.Argument(  # noqa: B008
        ...,
        help="Output path for backup file.",
    ),
) -> None:
    """
    Backup DMLClean data to a file.

    Backs up:
    - Configuration (config.toml)
    - Database (dml_clean.db)
    - History manifests

    Examples:

        dmlclean storage backup ./dmlclean-backup.zip
    """
    import shutil
    import tempfile

    console.print("[bold blue]Creating backup...[/bold blue]")

    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Copy config
            config_path = get_config_path()
            if config_path.exists():
                shutil.copy2(config_path, tmp_path / "config.toml")

            # Copy database
            db_path = get_db_path()
            if db_path.exists():
                shutil.copy2(db_path, tmp_path / "dml_clean.db")

            # Copy manifests
            manifests_dir = get_manifests_dir()
            if manifests_dir.exists():
                shutil.copytree(manifests_dir, tmp_path / "manifests")

            # Create zip
            backup_name = output_path.with_suffix("")
            shutil.make_archive(str(backup_name), "zip", tmp_path)

        console.print(f"[green]✓ Backup created:[/green] {output_path}")

    except Exception as e:
        console.print(f"[red]Backup failed:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("restore")
def storage_restore(
    backup_path: Path = typer.Argument(  # noqa: B008
        ...,
        help="Path to backup file to restore.",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """
    Restore DMLClean data from a backup file.

    WARNING: This will overwrite existing data!

    Examples:

        dmlclean storage restore ./dmlclean-backup.zip

        dmlclean storage restore ./dmlclean-backup.zip --yes
    """
    import shutil
    import tempfile
    import zipfile

    if not backup_path.exists():
        console.print(f"[red]Backup file not found:[/red] {backup_path}")
        raise typer.Exit(1)

    console.print("[bold yellow]⚠ Warning: This will overwrite existing data![/bold yellow]")

    if not yes:
        if not typer.confirm("Are you sure you want to restore?"):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Extract backup
            with zipfile.ZipFile(backup_path, "r") as zf:
                zf.extractall(tmp_path)

            # Restore config
            config_src = tmp_path / "config.toml"
            config_dst = get_config_path()
            if config_src.exists():
                config_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(config_src, config_dst)
                console.print("[green]✓ Config restored[/green]")

            # Restore database
            db_src = tmp_path / "dml_clean.db"
            db_dst = get_db_path()
            if db_src.exists():
                db_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(db_src, db_dst)
                console.print("[green]✓ Database restored[/green]")

            # Restore manifests
            manifests_src = tmp_path / "manifests"
            manifests_dst = get_manifests_dir()
            if manifests_src.exists():
                if manifests_dst.exists():
                    shutil.rmtree(manifests_dst)
                shutil.copytree(manifests_src, manifests_dst)
                console.print("[green]✓ Manifests restored[/green]")

        console.print(f"\n[green]✓ Restore complete from:[/green] {backup_path}")

    except Exception as e:
        console.print(f"[red]Restore failed:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("reset")
def storage_reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """
    Reset DMLClean storage to defaults.

    WARNING: This will delete ALL data including:
    - Configuration
    - Database (history, schedules)
    - Manifests
    - Cache

    Examples:

        dmlclean storage reset

        dmlclean storage reset --yes
    """
    console.print("[bold red]⚠ WARNING: This will delete ALL DMLClean data![/bold red]")
    console.print("\nThe following will be deleted:")
    console.print("  • Configuration (config.toml)")
    console.print("  • Database (dml_clean.db)")
    console.print("  • History and manifests")
    console.print("  • Cache files")
    console.print("\nThis action CANNOT be undone!")

    if not yes:
        if not typer.confirm("Are you ABSOLUTELY sure you want to reset?"):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    # Double confirmation
    if not yes:
        confirm = typer.prompt("Type 'RESET' to confirm")
        if confirm != "RESET":
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    try:
        import shutil

        base_dir = get_base_dir()

        if base_dir.exists():
            shutil.rmtree(base_dir)
            console.print("[green]✓ Storage reset complete.[/green]")
        else:
            console.print("[yellow]Storage directory does not exist.[/yellow]")

    except Exception as e:
        console.print(f"[red]Reset failed:[/red] {e}")
        raise typer.Exit(1) from e
