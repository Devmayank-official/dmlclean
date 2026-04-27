"""
Profile management command for DMLClean.

Manage cleaning profiles: list, show, create, clone, edit, delete, set-default.
Profiles are pre-configured category settings for different user types.
"""

from __future__ import annotations

import typer
from rich.table import Table

from dmlclean.cli.app import console
from dmlclean.config.loader import ConfigLoader
from dmlclean.config.profiles import get_profile, get_profiles, list_profiles

app = typer.Typer(help="Manage cleaning profiles.")


@app.callback(invoke_without_command=True)
def profile(
    ctx: typer.Context,
) -> None:
    """
    Manage cleaning profiles.

    Profiles are pre-configured sets of category settings optimized for
    specific user types or use cases.
    """
    if ctx.invoked_subcommand is None:
        _list_profiles()


@app.command("list")
def profile_list() -> None:
    """List all available profiles."""
    _list_profiles()


def _list_profiles() -> None:
    """List all available profiles."""
    profiles = get_profiles()

    if not profiles:
        console.print("[yellow]No profiles available.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Categories", justify="right")

    for name, profile in profiles.items():
        table.add_row(
            name,
            profile.description,
            str(len(profile.categories)),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(profiles)} profiles[/dim]")


@app.command("show")
def profile_show(
    name: str = typer.Argument(..., help="Profile name to show."),
) -> None:
    """
    Show details of a specific profile.

    Examples:

        dmlclean profile show developer

        dmlclean profile show system-admin
    """
    profile = get_profile(name)

    if not profile:
        console.print(f"[red]Profile not found:[/red] {name}")
        console.print(f"Available profiles: {', '.join(list_profiles())}")
        raise typer.Exit(1)

    console.print(f"[bold blue]Profile: {name}[/bold blue]\n")
    console.print(f"[bold]Description:[/bold] {profile.description}\n")

    # Settings table
    table = Table(show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Scan mode:", profile.scan_mode)
    table.add_row("Clean mode:", profile.clean_mode)
    table.add_row("Min age (days):", str(profile.min_age_days))
    table.add_row("Min size (MB):", str(profile.min_size_mb))

    console.print(table)

    # Categories
    console.print(f"\n[bold]Enabled Categories ({len(profile.enabled_categories)}):[/bold]")
    for cat in profile.enabled_categories:
        console.print(f"  • {cat}")


@app.command("create")
def profile_create(
    name: str = typer.Argument(..., help="New profile name."),
    description: str = typer.Option("", "--description", "-d", help="Profile description."),
) -> None:
    """
    Create a new profile from defaults.

    Examples:

        dmlclean profile create my-profile --description "My custom profile"
    """
    try:
        loader = ConfigLoader()
        loader.load()

        # Create new profile with defaults
        from dmlclean.models.profile import CleanProfile

        new_profile = CleanProfile(
            name=name,
            description=description or f"Custom profile: {name}",
            scan_mode="fast",
            clean_mode="dry-run",
            enabled_categories=["system_junk", "browser", "dev_python"],
        )

        # Save to config
        config = loader.to_dict()
        if "profiles" not in config:
            config["profiles"] = {}
        config["profiles"][name] = new_profile.model_dump()

        loader.save()

        console.print(f"[green]✓ Profile created:[/green] {name}")
        console.print(f"  Description: {new_profile.description}")
        console.print(f"  Categories: {', '.join(new_profile.enabled_categories)}")

    except Exception as e:
        console.print(f"[red]Failed to create profile:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("clone")
def profile_clone(
    source: str = typer.Argument(..., help="Source profile name."),
    dest: str = typer.Argument(..., help="Destination profile name."),
) -> None:
    """
    Clone an existing profile to create a new one.

    Examples:

        dmlclean profile clone developer my-dev-profile
    """
    source_profile = get_profile(source)

    if not source_profile:
        console.print(f"[red]Source profile not found:[/red] {source}")
        raise typer.Exit(1)

    try:
        loader = ConfigLoader()
        loader.load()

        from dmlclean.models.profile import CleanProfile

        cloned_profile = CleanProfile(
            name=dest,
            description=f"Cloned from {source}",
            scan_mode=source_profile.scan_mode,
            clean_mode=source_profile.clean_mode,
            enabled_categories=source_profile.enabled_categories,
            min_age_days=source_profile.min_age_days,
            min_size_mb=source_profile.min_size_mb,
        )

        config = loader.to_dict()
        if "profiles" not in config:
            config["profiles"] = {}
        config["profiles"][dest] = cloned_profile.model_dump()

        loader.save()

        console.print(f"[green]✓ Profile cloned:[/green] {source} → {dest}")

    except Exception as e:
        console.print(f"[red]Failed to clone profile:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("delete")
def profile_delete(
    name: str = typer.Argument(..., help="Profile name to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """
    Delete a custom profile.

    Built-in profiles (developer, designer, system-admin) cannot be deleted.

    Examples:

        dmlclean profile delete my-profile

        dmlclean profile delete my-profile --yes
    """
    # Check if profile exists
    profile = get_profile(name)
    if not profile:
        console.print(f"[red]Profile not found:[/red] {name}")
        raise typer.Exit(1)

    # Check if built-in
    built_in_profiles = ["developer", "designer", "system-admin", "gamer", "minimal"]
    if name in built_in_profiles:
        console.print(f"[red]Cannot delete built-in profile:[/red] {name}")
        raise typer.Exit(1)

    # Confirm
    if not yes:
        if not typer.confirm(f"Are you sure you want to delete profile '{name}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    try:
        loader = ConfigLoader()
        loader.load()

        config = loader.to_dict()
        if "profiles" in config and name in config["profiles"]:
            del config["profiles"][name]
            loader.save()

        console.print(f"[green]✓ Profile deleted:[/green] {name}")

    except Exception as e:
        console.print(f"[red]Failed to delete profile:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("set-default")
def profile_set_default(
    name: str = typer.Argument(..., help="Profile name to set as default."),
) -> None:
    """
    Set the default profile for cleaning operations.

    Examples:

        dmlclean profile set-default developer
    """
    profile = get_profile(name)

    if not profile:
        console.print(f"[red]Profile not found:[/red] {name}")
        raise typer.Exit(1)

    try:
        loader = ConfigLoader()
        loader.load()
        loader.set("general", "default_profile", name)
        loader.save()

        console.print(f"[green]✓ Default profile set:[/green] {name}")

    except Exception as e:
        console.print(f"[red]Failed to set default profile:[/red] {e}")
        raise typer.Exit(1) from e
