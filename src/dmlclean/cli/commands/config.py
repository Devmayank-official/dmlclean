"""
Config command for DMLClean.

Manages DMLClean configuration with get, set, and reset operations.
"""

from __future__ import annotations

import typer

from dmlclean.cli.app import console
from dmlclean.config.loader import ConfigLoader

app = typer.Typer(help="Manage configuration.")


@app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key (e.g., 'general.default_scan_mode')."),
) -> None:
    """Get a config value."""
    try:
        loader = ConfigLoader()
        loader.load()

        parts = key.split(".")
        value = loader.to_dict()

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                console.print(f"[red]Key not found:[/red] {key}")
                raise typer.Exit(1)

        console.print(f"{key} = {value}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key."),
    value: str = typer.Argument(..., help="Config value."),
) -> None:
    """Set a config value."""
    try:
        loader = ConfigLoader()
        loader.load()

        parts = key.split(".")
        config = loader.to_dict()

        # Navigate to section
        section = parts[0]
        if section not in config:
            console.print(f"[red]Invalid section:[/red] {section}")
            raise typer.Exit(1)

        config_key = parts[1] if len(parts) > 1 else key
        loader.set(section, config_key, value)
        loader.save()

        console.print(f"[green]✓ Set[/green] {key} = {value}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("reset")
def config_reset() -> None:
    """Reset configuration to defaults."""
    if not typer.confirm("Are you sure you want to reset all settings to defaults?"):
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(0)

    try:
        loader = ConfigLoader()
        loader.load()

        # Delete config file
        if loader.config_path.exists():
            loader.config_path.unlink()
            console.print("[green]✓ Configuration reset to defaults.[/green]")
        else:
            console.print("[yellow]No custom configuration to reset.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("validate")
def config_validate() -> None:
    """Validate the configuration file."""
    import sys

    try:
        loader = ConfigLoader()
        loader.load()

        is_valid, errors = loader.validate()

        if is_valid:
            console.print("[green]✓ Configuration is valid.[/green]")
            console.print(f"  Location: {loader.config_path}")
            sys.exit(0)
        else:
            console.print("[red]✗ Configuration is invalid:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command("edit")
def config_edit() -> None:
    """Open configuration file in editor."""
    import subprocess
    import sys

    loader = ConfigLoader()

    # Ensure file exists
    loader.config_path.parent.mkdir(parents=True, exist_ok=True)
    if not loader.config_path.exists():
        loader.load()
        loader.save()

    editor = None
    if sys.platform == "win32":
        editor = "notepad"
    else:
        # ruff: noqa: S605  # safe: finding editor in PATH
        editor = (
            subprocess.getoutput("which nano")
            or subprocess.getoutput("which vim")
            or subprocess.getoutput("which vi")
            or "$EDITOR"
        )

    try:
        subprocess.run([editor, str(loader.config_path)])
    except Exception as e:
        console.print(f"[red]Failed to open editor: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("show")
def config_show(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format"),
) -> None:
    """Print full resolved configuration."""
    try:
        loader = ConfigLoader()
        loader.load()

        config = loader.to_dict()

        if json_output:
            import json

            print(json.dumps(config, indent=2))
        else:
            console.print("[bold]DMLClean Configuration[/bold]\n")
            for section, values in config.items():
                console.print(f"[bold cyan]{section}[/bold cyan]")
                if isinstance(values, dict):
                    for key, value in values.items():
                        console.print(f"  {key}: {value}")
                else:
                    console.print(f"  {values}")
                console.print()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
