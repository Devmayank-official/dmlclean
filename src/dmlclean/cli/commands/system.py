"""
System commands for DML Clean.

Version info, system info, self-update, and shell completion generation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table

from dmlclean import __version__ as CURRENT_VERSION  # noqa: N812
from dmlclean.cli.app import console
from dmlclean.utils.platform import get_platform

app = typer.Typer(help="System commands.")


@app.command("info")
def system_info(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed system information.",
    ),
) -> None:
    """
    Show detailed system information in the exact DML Nexus architectural style.
    """
    import platform
    import psutil
    from dmlclean.utils.sizes import humanize_size
    from dmlclean.storage.paths import get_config_dir, get_data_dir, get_logs_dir

    # Top Identity Header (Cyan Bold)
    console.print(f"[bold cyan]DML Clean: Enterprise-Ready Storage Optimization & Lifecycle Orchestrator v{CURRENT_VERSION}[/bold cyan]")
    
    # Sub-header (Normal Left Aligned)
    console.print("[italic]System Information[/italic]\n")

    # Table matching Nexus Screenshot DNA
    table = Table(
        show_header=False, 
        box=box.ROUNDED, 
        border_style="white", 
        padding=(0, 1),
        collapse_padding=True
    )
    table.add_column("Attribute", style="bold white", width=20)
    table.add_column("Value", style="white")

    # Application details
    table.add_row("Application", "DML Clean: Enterprise-Ready Storage Orchestrator")
    table.add_row("Version", CURRENT_VERSION)
    table.add_row("Author", "DML Labs")
    table.add_row("Credit", "Developed by DML Labs")
    table.add_row("Lead Engineer", "devmayank-official")
    table.add_row("Repository", "https://github.com/Devmayank-official/dmlclean")
    table.add_row("GitHub", "https://github.com/devmayank-official")
    table.add_row("Contact", "devmayank.inbox@gmail.com")
    
    # Environment info
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python Version", python_version)
    table.add_row("Platform", platform.platform())
    table.add_row("Architecture", "64bit" if sys.maxsize > 2**32 else "32bit")

    # Storage Paths
    table.add_row("Config Dir", str(get_config_dir()))
    table.add_row("Data Dir", str(get_data_dir()))
    table.add_row("Log Dir", str(get_logs_dir()))

    console.print(table)

    if verbose:
        console.print("\n[bold cyan]Additional Telemetry:[/bold cyan]")
        mem = psutil.virtual_memory()
        console.print(f"  [bold]RAM:[/bold] {humanize_size(mem.total)} ({mem.percent}% used)")
        
        console.print("\n[bold]Disk Vectors:[/bold]")
        for partition in psutil.disk_partitions()[:3]:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                console.print(f"  {partition.device}: {usage.percent}% [{humanize_size(usage.used)}/{humanize_size(usage.total)}]")
            except PermissionError:
                pass


@app.command("version")
def version_cmd(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed version information.",
    ),
) -> None:
    """
    Show version info in the DML Stream identity card style.
    """
    content = (
        f"[bold blue]DML Clean[/bold blue] v{CURRENT_VERSION}\n"
        f"[dim]Enterprise-Ready Storage Optimization & Lifecycle Orchestrator[/dim]"
    )
    
    if verbose:
        platform_info = get_platform()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        content += f"\n\n[bold white]Environment:[/bold white]\n"
        content += f"Platform: [cyan]{platform_info}[/cyan]\n"
        content += f"Python:   [yellow]{python_version}[/yellow]"

    console.print(
        Panel(
            content, 
            expand=False, 
            border_style="blue",
            padding=(1, 2)
        )
    )


@app.command("completion")
def completion(
    shell: str = typer.Argument(
        "bash",
        help="Shell type: bash, zsh, fish, or powershell",
    ),
) -> None:
    """Generate shell completion script."""
    valid_shells = ("bash", "zsh", "fish", "powershell")

    if shell not in valid_shells:
        console.print(f"[red]Invalid shell: {shell}[/red]")
        raise typer.Exit(1)

    from dmlclean.cli.app import app as main_app
    
    if shell == "bash":
        from typer.completion import BashComplete
        complete = BashComplete(main_app, {}, "dmlclean", "_DMLCLEAN_COMPLETE")
        print(complete.source())
    elif shell == "zsh":
        from typer.completion import ZshComplete
        complete = ZshComplete(main_app, {}, "dmlclean", "_DMLCLEAN_COMPLETE")
        print(complete.source())
    elif shell == "fish":
        from typer.completion import FishComplete
        complete = FishComplete(main_app, {}, "dmlclean", "_DMLCLEAN_COMPLETE")
        print(complete.source())
    elif shell == "powershell":
        from typer.completion import PowerShellComplete
        complete = PowerShellComplete(main_app, {}, "dmlclean", "_DMLCLEAN_COMPLETE")
        print(complete.source())


@app.command("self-update")
def self_update(
    check: bool = typer.Option(
        False,
        "--check",
        help="Only check for updates, don't install.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force update even if already latest version.",
    ),
) -> None:
    """Update DML Clean via pipx or pip."""
    console.print("[bold blue]Checking for updates...[/bold blue]")

    try:
        from dmlclean.cli.middleware.update_check import UpdateCheckMiddleware
        middleware = UpdateCheckMiddleware(console)
        version_info = middleware.check_for_updates_sync()

        if version_info:
            console.print(f"[green]✓ Current:[/green] {CURRENT_VERSION}")
            console.print(f"[green]✓ Latest:[/green] {version_info.latest_version}")
            if check: return
            if not force and version_info.latest_version == CURRENT_VERSION:
                console.print("[green]✓ Already at latest version.[/green]")
                return
    except Exception as e:
        console.print(f"[yellow]Update check failed: {e}[/yellow]")

    import subprocess
    try:
        result = subprocess.run(["pipx", "list"], capture_output=True, text=True)
        if "dmlclean" in result.stdout.lower():
            subprocess.run(["pipx", "upgrade", "dmlclean"])
            return
    except FileNotFoundError:
        pass

    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "dmlclean"])
