"""
Schedule command for DMLClean.

Manages scheduled cleaning operations.
Uses ScheduleRequest/ScheduleEntry DTOs for type-safe operations.

Developed by DML Labs
Lead Engineer: Github/Devmayank-official
Project URL: https://github.com/Devmayank-official/dml-clean
"""

from __future__ import annotations

import typer
from rich.table import Table

from dmlclean.cli.app import console
from dmlclean.container import get_container

app = typer.Typer(help="Manage scheduled cleaning operations.")


def _get_service() -> ScheduleService:
    """Get ScheduleService instance from container."""
    container = get_container()
    return container.schedule_service


@app.command("add")
def schedule_add(
    name: str = typer.Option(..., "--name", "-n", help="Name for this schedule."),
    cron_expression: str = typer.Option(
        ..., "--cron", "-c", help="Cron expression (e.g., '0 3 * * *' for daily at 3 AM)."
    ),
    mode: str = typer.Option("trash", "--mode", "-m", help="Clean mode."),
    categories: str = typer.Option("", "--categories", help="Categories to clean."),
    profile: str = typer.Option("developer", "--profile", "-p", help="Cleaning profile."),
) -> None:
    """Add a new cleaning schedule.

    Examples:
        # Daily cleanup at 3 AM
        dmlclean schedule add -n "Daily Cleanup" -c "0 3 * * *"

        # Weekly cleanup on Sunday at 2 AM
        dmlclean schedule add -n "Weekly Cleanup" -c "0 2 * * 0" --profile system-admin

    Note: Cron expressions with special characters (*, ?, etc.) should be quoted in shell.
    """
    from croniter import croniter

    service = _get_service()
    category_list = [c.strip() for c in categories.split(",") if c.strip()]

    # Validate cron expression
    try:
        croniter(cron_expression)
    except Exception as e:
        console.print(f"[red]Invalid cron expression:[/red] {cron_expression}")
        console.print(f"Error: {e}")
        console.print("\n[dim]Examples of valid cron expressions:[/dim]")
        console.print("  '0 3 * * *'     - Daily at 3 AM")
        console.print("  '0 2 * * 0'     - Weekly on Sunday at 2 AM")
        console.print("  '*/15 * * * *'  - Every 15 minutes")
        console.print("\n[dim]Tip: Always quote cron expressions in shell![/dim]")
        raise typer.Exit(1)

    entry = service.create_schedule(
        name=name,
        cron_expression=cron_expression,
        profile=profile,
        clean_mode=mode,
        categories=category_list,
        enabled=True,
    )

    console.print(f"[green]✓ Schedule added:[/green] {name} (ID: {entry.id})")
    console.print(f"  Cron: {entry.cron_expression}")
    if entry.next_run:
        console.print(f"  Next run: {entry.next_run[:19].replace('T', ' ')}")


@app.command("remove")
def schedule_remove(
    job_id: str = typer.Option(..., "--id", help="Job ID to remove."),
) -> None:
    """Remove a scheduled job by ID.

    Examples:
        dmlclean schedule remove --id abc123
    """
    service = _get_service()

    if service.remove_schedule(job_id):
        console.print(f"[green]✓ Schedule removed:[/green] {job_id}")
    else:
        console.print(f"[red]Job not found:[/red] {job_id}")


@app.command("list")
def schedule_list(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format."),
    all_entries: bool = typer.Option(False, "--all", help="List all entries (including disabled)."),
) -> None:
    """List all scheduled jobs."""
    import sys

    service = _get_service()

    try:
        entries = service.list_schedules()
    except Exception as e:
        console.print(f"[red]Failed to list schedules: {e}[/red]")
        sys.exit(1)

    if not entries:
        console.print("[yellow]No scheduled jobs.[/yellow]")
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
    table.add_column("Name")
    table.add_column("Cron Expression")
    table.add_column("Mode")
    table.add_column("Next Run")
    table.add_column("Status")

    for entry in entries:
        status = "[green]Active[/green]" if entry.enabled else "[yellow]Paused[/yellow]"
        next_run = entry.next_run[:19].replace("T", " ") if entry.next_run else "N/A"
        table.add_row(
            entry.id[:8],
            entry.name,
            entry.cron_expression,
            entry.clean_mode,
            next_run,
            status,
        )

    console.print(table)
    sys.exit(0)


@app.command("enable")
def schedule_enable(
    job_id: str = typer.Argument(..., help="Job ID to enable."),
) -> None:
    """Enable a scheduled job."""
    service = _get_service()

    if service.enable_schedule(job_id):
        console.print(f"[green]✓ Schedule enabled:[/green] {job_id}")
    else:
        console.print(f"[red]Failed to enable:[/red] {job_id}")


@app.command("disable")
def schedule_disable(
    job_id: str = typer.Argument(..., help="Job ID to disable."),
) -> None:
    """Disable a scheduled job."""
    service = _get_service()

    if service.disable_schedule(job_id):
        console.print(f"[green]✓ Schedule disabled:[/green] {job_id}")
    else:
        console.print(f"[red]Failed to disable:[/red] {job_id}")


@app.command("install")
def schedule_install(
    job_id: str = typer.Argument(..., help="Job ID to install as native task."),
) -> None:
    """Install a schedule as a native OS task (cron/Task Scheduler)."""
    service = _get_service()

    if service.install_native_task(job_id):
        console.print(f"[green]✓ Installed as native task:[/green] {job_id}")
    else:
        console.print(f"[red]Failed to install:[/red] {job_id}")


@app.command("uninstall")
def schedule_uninstall(
    job_id: str = typer.Argument(..., help="Job ID to uninstall."),
) -> None:
    """Remove a native OS scheduled task."""
    service = _get_service()

    if service.uninstall_native_task(job_id):
        console.print(f"[green]✓ Uninstalled native task:[/green] {job_id}")
    else:
        console.print(f"[red]Failed to uninstall:[/red] {job_id}")


@app.command("start")
def schedule_start(
    foreground: bool = typer.Option(
        False, "--foreground", "-f", help="Run in foreground (blocking)."
    ),
) -> None:
    """Start the scheduler.

    This starts the APScheduler to execute scheduled jobs.
    By default, starts in background (non-blocking).

    Examples:
        # Start scheduler (background)
        dmlclean schedule start

        # Start scheduler (foreground, for debugging)
        dmlclean schedule start --foreground
    """
    from dmlclean.core.scheduler import Scheduler
    from dmlclean.storage import get_database

    console.print("[bold blue]Starting scheduler...[/bold blue]")

    db = get_database()
    scheduler = Scheduler(db)

    # Load and start scheduler
    scheduler.start()

    console.print("[green]✓ Scheduler started[/green]")
    console.print(f"  Loaded {len(scheduler._jobs)} job(s)")
    console.print(f"  Running in {'foreground' if foreground else 'background'} mode")

    if foreground:
        # Block and keep running
        console.print("\n[yellow]Press Ctrl+C to stop[/yellow]")
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Scheduler stopped[/yellow]")
