# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Notification management commands for DMLClean.

Manage desktop notifications: list backends, send test notifications, configure settings.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

import typer
from rich.table import Table

from dmlclean.cli.app import console

app = typer.Typer(help="Manage desktop notifications.")


@app.callback(invoke_without_command=True)
def notification(
    ctx: typer.Context,
) -> None:
    """
    Notification management commands.

    List backends, send test notifications, configure settings.
    """
    if ctx.invoked_subcommand is None:
        _list_backends()


def _list_backends() -> None:
    """List available notification backends."""
    from dmlclean.notifications.backends.desktop import DesktopNotifierBackend
    from dmlclean.notifications.backends.dummy import DummyBackend
    from dmlclean.notifications.backends.plyer_backend import PlyerBackend

    backends = [
        (
            "Desktop Notifier",
            DesktopNotifierBackend().available,
            "Primary desktop notifications (Windows/macOS/Linux)",
        ),
        ("Plyer", PlyerBackend().available, "Cross-platform fallback (Android/iOS/Windows)"),
        ("Dummy", DummyBackend().available, "No-op for testing/development"),
    ]

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Backend", style="cyan")
    table.add_column("Available", justify="center")
    table.add_column("Description")

    for name, available, desc in backends:
        status = "[green]✓[/green]" if available else "[red]✗[/red]"
        table.add_row(name, status, desc)

    console.print(table)
    console.print("\n[dim]Backends are tried in order until one succeeds.[/dim]")


@app.command("list")
def notification_list() -> None:
    """List available notification backends."""
    _list_backends()


@app.command("test")
def notification_test(
    title: str = typer.Option("DMLClean Test", "--title", "-t", help="Notification title"),
    message: str = typer.Option(
        "This is a test notification from DMLClean. If you see this, notifications are working!",
        "--message",
        "-m",
        help="Notification message",
    ),
    timeout: int = typer.Option(5, "--timeout", "-T", help="Notification timeout in seconds"),
) -> None:
    """Send a test notification."""
    from dmlclean.notifications.notifier import Notifier

    console.print("[bold blue]Sending test notification...[/bold blue]")
    console.print(f"  Title: {title}")
    console.print(f"  Message: {message[:50]}...")
    console.print(f"  Timeout: {timeout}s")

    notifier = Notifier()
    success = notifier.send_sync(title=title, message=message, timeout=timeout)

    if success:
        console.print("\n[green]✓ Test notification sent successfully![/green]")
        console.print("[dim]Check your desktop for the notification.[/dim]")
    else:
        console.print("\n[yellow]⚠ Notification backend reported failure[/yellow]")
        console.print("[dim]This may be normal if no notification backend is available.[/dim]")


@app.command("config")
def notification_config() -> None:
    """Show notification configuration."""
    from dmlclean.container import get_container

    container = get_container()
    config = container.config.schema

    console.print("[bold blue]Notification Configuration[/bold blue]\n")

    if hasattr(config, "notifications") and config.notifications:
        console.print(
            f"[bold]Enabled:[/bold] {getattr(config.notifications, 'enabled', 'unknown')}"
        )
        console.print(f"[bold]Desktop:[/bold] {getattr(config.notifications, 'desktop', 'N/A')}")
        console.print(f"[bold]Sound:[/bold] {getattr(config.notifications, 'sound', 'N/A')}")
    else:
        console.print("[yellow]No notification configuration found.[/yellow]")
        console.print("[dim]Using default settings.[/dim]")

    console.print("\n[dim]Configure notifications in config.toml:[/dim]")
    console.print("[dim]  [notifications][/dim]")
    console.print("[dim]  enabled = true[/dim]")
    console.print("[dim]  desktop = true[/dim]")
    console.print("[dim]  sound = false[/dim]")
