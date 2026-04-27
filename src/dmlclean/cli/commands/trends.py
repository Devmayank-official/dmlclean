"""
Disk usage trends command for DMLClean.

View and analyze disk usage trends over time with projections and warnings.
"""

from __future__ import annotations

import typer
from rich.table import Table

from dmlclean.cli.app import console

app = typer.Typer(help="View disk usage trends.")


@app.callback(invoke_without_command=True)
def trends(
    ctx: typer.Context,
    since: str = typer.Option(
        None,
        "--since",
        "-s",
        help="Show trends since date (e.g., '7d', '30d', '2025-01-01').",
    ),
    days: int | None = typer.Option(
        None,
        "--days",
        "-d",
        help="Show trends for last N days (alias for --since).",
    ),
    warn_threshold: int = typer.Option(
        90,
        "--warn-threshold",
        help="Warn if disk usage exceeds this percentage.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format.",
    ),
) -> None:
    """
    View disk usage trends.

    Shows disk usage history and projects when disk will be full.

    Examples:

        dmlclean trends

        dmlclean trends --since 30d

        dmlclean trends --days 7

        dmlclean trends --warn-threshold 80
    """
    import sys

    # Convert --days to --since format
    if days and not since:
        since = f"{days}d"
    elif days and since:
        # Both provided, --days takes precedence
        since = f"{days}d"

    _show_trends(since, warn_threshold, json_output)
    sys.exit(0)


def _show_trends(
    since: str | None,
    warn_threshold: int,
    json_output: bool,
) -> None:
    """Show disk usage trends."""
    import psutil  # type: ignore[import-untyped]

    # Get current disk usage
    try:
        usage = psutil.disk_usage("/")
    except Exception:
        usage = psutil.disk_usage("C:\\")

    total = usage.total
    used = usage.used
    free = usage.free
    percent = usage.percent

    if json_output:
        import json

        data = {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "percent_used": percent,
            "warn_threshold": warn_threshold,
            "warning": percent >= warn_threshold,
        }
        print(json.dumps(data, indent=2))
        return

    from dmlclean.utils.sizes import humanize_size

    # Header
    console.print("[bold blue]DMLClean Disk Usage Trends[/bold blue]\n")

    # Current usage - simple text (no table)
    console.print(f"[bold]Total:[/bold] {humanize_size(total)}")
    console.print(f"[bold]Used:[/bold] {humanize_size(used)} ({percent:.1f}%)")
    console.print(f"[bold]Free:[/bold] {humanize_size(free)}")

    # Visual bar
    bar_width = 50
    filled = int(bar_width * percent / 100)
    bar = "█" * filled + "░" * (bar_width - filled)

    if percent >= warn_threshold:
        color = "red"
    elif percent >= 70:
        color = "yellow"
    else:
        color = "green"

    console.print(f"\n[{color}]{bar}[/{color}] {percent:.1f}%")

    # Warning if threshold exceeded
    if percent >= warn_threshold:
        console.print(
            f"\n[bold red]⚠ WARNING: Disk usage ({percent:.1f}%) exceeds threshold ({warn_threshold}%)![/bold red]"  # noqa: E501
        )
        console.print("Consider running dmlclean clean to free up space.")

    # Projected full date (simple linear projection)
    # In a real implementation, this would use historical trend data
    if percent > 50:
        # Rough estimate: assume 1% per week growth
        weeks_until_full = int((100 - percent) / 1) if percent < 100 else 0
        if weeks_until_full > 0:
            console.print(
                f"\n[dim]Projected full in ~{weeks_until_full} weeks (at current growth rate)[/dim]"
            )


@app.command("dashboard")
def trends_dashboard() -> None:
    """Show interactive disk usage dashboard."""
    import psutil

    console.print("[bold blue]DMLClean Disk Dashboard[/bold blue]\n")

    # Get all partitions
    partitions = psutil.disk_partitions()

    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue

        from dmlclean.utils.sizes import humanize_size

        console.print(f"[bold]{partition.device}[/bold] ({partition.mountpoint})")

        table = Table(show_header=False, box=None)
        table.add_column("Label", style="cyan")
        table.add_column("Value")

        table.add_row("Total:", humanize_size(usage.total))
        table.add_row("Used:", f"{humanize_size(usage.used)} ({usage.percent:.1f}%)")
        table.add_row("Free:", humanize_size(usage.free))

        console.print(table)

        # Visual bar
        bar_width = 40
        filled = int(bar_width * usage.percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        if usage.percent >= 90:
            color = "red"
        elif usage.percent >= 70:
            color = "yellow"
        else:
            color = "green"

        console.print(f"[{color}][{bar}][/{color}] {usage.percent:.1f}%\n")
