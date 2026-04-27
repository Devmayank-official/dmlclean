"""
Plugin management command for DMLClean.

Manage cleaning plugins: list, enable, disable, info, scan.
Supports built-in plugins and third-party plugin installation.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

import typer
from rich.table import Table

from dmlclean.cli.app import console
from dmlclean.plugins.builtin import get_all_plugins, get_plugin_by_name
from dmlclean.services import PluginService

app = typer.Typer(help="Manage cleaning plugins.")


def _get_service() -> PluginService:
    """Get PluginService instance."""
    return PluginService()


@app.callback(invoke_without_command=True)
def plugin(
    ctx: typer.Context,
) -> None:
    """
    Manage cleaning plugins.

    List, enable, disable, and get information about cleaning plugins.
    """
    if ctx.invoked_subcommand is None:
        _list_plugins()


def _list_plugins(json_output: bool = False) -> None:
    """List all available plugins."""
    # Get built-in plugins
    plugin_classes = get_all_plugins()
    plugins = []
    for plugin_class in plugin_classes:
        plugin = plugin_class()
        plugins.append(
            {
                "name": plugin.name,
                "description": plugin.description,
                "default_enabled": plugin.default_enabled,
                "risk_level": plugin.risk_level.value,
            }
        )

    if json_output:
        import json

        print(json.dumps({"plugins": plugins}, indent=2))
        return

    # Simple text output (no table - avoids rendering issues)
    console.print("\n[bold]Available Plugins:[/bold]")
    for p in plugins:
        enabled_str = "✓" if p["default_enabled"] else "✗"
        risk_str = str(p["risk_level"]).upper()
        console.print(f"  {enabled_str} {p['name']}: {p['description']} [{risk_str}]")

    console.print(f"\n[dim]Total: {len(plugins)} built-in plugins[/dim]")


@app.command("list")
def plugin_list(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """List all available plugins."""
    _list_plugins(json_output)


@app.command("info")
def plugin_info(
    name: str = typer.Argument(..., help="Plugin name to get info about."),
) -> None:
    """
    Show detailed information about a plugin.

    Examples:

        dmlclean plugin info browser

        dmlclean plugin info dev_python
    """
    plugin_class = get_plugin_by_name(name)
    if plugin_class is None:
        console.print(f"[red]Plugin not found:[/red] {name}")
        available = [p().name for p in get_all_plugins()]
        console.print(f"Available plugins: {', '.join(available)}")
        raise typer.Exit(1)

    plugin = plugin_class()

    console.print(f"[bold blue]Plugin: {plugin.name}[/bold blue]\n")
    console.print(f"[bold]Description:[/bold] {plugin.description}")
    console.print(f"[bold]Default Enabled:[/bold] {'Yes' if plugin.default_enabled else 'No'}")
    console.print(f"[bold]Risk Level:[/bold] {plugin.risk_level.value}")


@app.command("enable")
def plugin_enable(
    name: str = typer.Argument(..., help="Plugin name to enable."),
) -> None:
    """
    Enable a plugin in configuration.

    Examples:

        dmlclean plugin enable dev_node
    """
    from dmlclean.config.loader import ConfigLoader

    plugin_class = get_plugin_by_name(name)
    if plugin_class is None:
        console.print(f"[red]Plugin not found:[/red] {name}")
        raise typer.Exit(1)

    try:
        loader = ConfigLoader()
        loader.load()

        config = loader.to_dict()
        if "categories" not in config:
            config["categories"] = {}

        if name not in config["categories"]:
            config["categories"][name] = {}
        config["categories"][name]["enabled"] = True

        loader.save()

        console.print(f"[green]✓ Plugin enabled:[/green] {name}")

    except Exception as e:
        console.print(f"[red]Failed to enable plugin:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("disable")
def plugin_disable(
    name: str = typer.Argument(..., help="Plugin name to disable."),
) -> None:
    """
    Disable a plugin in configuration.

    Examples:

        dmlclean plugin disable dev_node
    """
    from dmlclean.config.loader import ConfigLoader

    plugin_class = get_plugin_by_name(name)
    if plugin_class is None:
        console.print(f"[red]Plugin not found:[/red] {name}")
        raise typer.Exit(1)

    try:
        loader = ConfigLoader()
        loader.load()

        config = loader.to_dict()
        if "categories" not in config:
            config["categories"] = {}

        if name not in config["categories"]:
            config["categories"][name] = {}
        config["categories"][name]["enabled"] = False

        loader.save()

        console.print(f"[green]✓ Plugin disabled:[/green] {name}")

    except Exception as e:
        console.print(f"[red]Failed to disable plugin:[/red] {e}")
        raise typer.Exit(1) from e


@app.command("install")
def plugin_install(
    name: str = typer.Argument(..., help="Plugin name to install."),
    version: str | None = typer.Option(None, "--version", help="Specific version to install."),
) -> None:
    """
    Install a plugin from the registry.

    Examples:

        dmlclean plugin install aws-cleanup
    """
    service = _get_service()

    console.print(f"[bold blue]Installing plugin:[/bold blue] {name}")

    result = service.install(name, version=version or None)

    if result.get("success"):
        console.print(f"[green]✓ Plugin installed:[/green] {name} v{result.get('version')}")
    else:
        console.print(f"[red]Failed to install:[/red] {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)


@app.command("uninstall")
def plugin_uninstall(
    name: str = typer.Argument(..., help="Plugin name to uninstall."),
) -> None:
    """
    Uninstall a plugin.

    Examples:

        dmlclean plugin uninstall aws-cleanup
    """
    service = _get_service()

    console.print(f"[bold blue]Uninstalling plugin:[/bold blue] {name}")

    result = service.uninstall(name)

    if result.get("success"):
        console.print(f"[green]✓ Plugin uninstalled:[/green] {name}")
    else:
        console.print(f"[red]Failed to uninstall:[/red] {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)


@app.command("update")
def plugin_update(
    name: str | None = typer.Argument(None, help="Plugin name to update (all if not specified)."),
) -> None:
    """
    Update plugin(s).

    Examples:

        dmlclean plugin update          # Update all
        dmlclean plugin update aws      # Update specific
    """
    service = _get_service()

    console.print("[bold blue]Updating plugins...[/bold blue]")

    result = service.update(name=name if name else None)

    if result.get("success"):
        console.print("[green]✓ Plugins updated[/green]")
    else:
        console.print("[yellow]Some plugins failed to update[/yellow]")


@app.command("search")
def plugin_search(
    query: str = typer.Argument(..., help="Search query."),
) -> None:
    """
    Search for plugins.

    Examples:

        dmlclean plugin search aws
        dmlclean plugin search cloud
    """
    service = _get_service()

    results = service.search(query)

    if not results:
        console.print(f"[yellow]No plugins found for:[/yellow] {query}")
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Author")
    table.add_column("Verified")

    for plugin in results:
        verified = "✅" if plugin.get("verified") else ""
        table.add_row(
            plugin.get("name", "N/A"),
            plugin.get("description", "N/A")[:50],
            plugin.get("author", "N/A"),
            verified,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} plugin(s)[/dim]")
