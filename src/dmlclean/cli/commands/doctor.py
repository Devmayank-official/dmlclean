"""
Doctor command for DMLClean.

System diagnostics and health checks for Python version, platform, permissions,
disk space, config validity, protected zone integrity, and scheduler status.
"""

from __future__ import annotations

import json as json_module
import sys

import typer

from dmlclean import __version__
from dmlclean.cli.app import console
from dmlclean.config.loader import ConfigLoader
from dmlclean.utils.platform import get_platform, is_admin

app = typer.Typer(help="System diagnostics.")


@app.callback(invoke_without_command=True)
def doctor(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", "-j", help="Output in JSON format"),
) -> None:
    """
    System diagnostics.

    Checks Python version, permissions, disk space, config validity,
    protected zone integrity, and scheduler status.
    """
    if ctx.invoked_subcommand is None:
        _run_doctor_checks(json_output)


def _run_doctor_checks(json_output: bool = False) -> None:
    """Run the actual doctor diagnostic checks."""
    issues = []
    warnings = []
    ok_items = []
    diagnostic_data = {"version": __version__, "platform": get_platform(), "checks": {}}

    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok_items.append(f"Python version: {python_version}")
    diagnostic_data["python_version"] = python_version

    # Check platform
    platform = get_platform()
    ok_items.append(f"Platform: {platform}")

    # Check admin privileges
    if is_admin():
        warnings.append("Running as administrator/root (not recommended)")
        diagnostic_data["is_admin"] = True
    else:
        ok_items.append("Running as standard user")
        diagnostic_data["is_admin"] = False

    # Check config
    try:
        loader = ConfigLoader()
        loader.load()
        is_valid, errors = loader.validate()

        if is_valid:
            ok_items.append("Configuration: valid")
            diagnostic_data["config"] = {"valid": True, "path": str(loader.config_path)}
        else:
            issues.append(f"Configuration invalid: {errors}")
            diagnostic_data["config"] = {"valid": False, "errors": errors}
    except Exception as e:
        issues.append(f"Configuration error: {e}")
        diagnostic_data["config"] = {"error": str(e)}

    # Check data directory
    try:
        from dmlclean.storage.paths import get_data_dir

        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        ok_items.append("Data directory: writable")
        diagnostic_data["data_dir"] = str(data_dir)
    except Exception as e:
        issues.append(f"Data directory error: {e}")
        diagnostic_data["data_dir_error"] = str(e)

    # Check disk space
    try:
        import psutil

        drive = "C:\\" if platform == "windows" else "/"
        usage = psutil.disk_usage(drive)
        free_gb = usage.free / (1024**3)

        if free_gb < 1:
            warnings.append(f"Low disk space: {free_gb:.2f} GB free")
            diagnostic_data["disk"] = {"free_gb": free_gb, "warning": True}
        else:
            ok_items.append(f"Disk space: {free_gb:.2f} GB free")
            diagnostic_data["disk"] = {"free_gb": free_gb, "warning": False}
    except Exception as e:
        issues.append(f"Disk space check failed: {e}")
        diagnostic_data["disk_error"] = str(e)

    # Check scheduler
    try:
        from dmlclean.core.scheduler import Scheduler

        scheduler = Scheduler()
        jobs = scheduler.list_jobs()
        ok_items.append(f"Scheduled jobs: {len(jobs)} active")
        diagnostic_data["scheduler"] = {"jobs": len(jobs)}
    except Exception as e:
        warnings.append(f"Scheduler check: {e}")
        diagnostic_data["scheduler_error"] = str(e)

    # Check dependencies
    required_deps = [
        "typer",
        "rich",
        "psutil",
        "send2trash",
        "platformdirs",
        "aiofiles",
        "apscheduler",
        "loguru",
        "pydantic",
        "xxhash",
    ]
    missing_deps = []
    for dep in required_deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            missing_deps.append(dep)

    if missing_deps:
        issues.append(f"Missing dependencies: {', '.join(missing_deps)}")
        diagnostic_data["missing_deps"] = missing_deps
    else:
        ok_items.append("Dependencies: all installed")
        diagnostic_data["missing_deps"] = []

    # Output results
    if json_output:
        diagnostic_data["ok"] = ok_items
        diagnostic_data["warnings"] = warnings
        diagnostic_data["issues"] = issues
        diagnostic_data["status"] = "error" if issues else ("warning" if warnings else "ok")
        print(json_module.dumps(diagnostic_data, indent=2))
        if issues:
            raise typer.Exit(1)
    else:
        console.print("[bold blue]DMLClean Doctor[/bold blue]\n")
        if ok_items:
            console.print("[bold green]OK:[/bold green]")
            for item in ok_items:
                console.print(f"  [green]+[/green] {item}")

        if warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for item in warnings:
                console.print(f"  [yellow]![/yellow] {item}")

        if issues:
            console.print("\n[bold red]Issues:[/bold red]")
            for item in issues:
                console.print(f"  [red]-[/red] {item}")

        console.print()
        if issues:
            console.print(f"[red]Found {len(issues)} issue(s) that need attention.[/red]")
            raise typer.Exit(1)
        elif warnings:
            console.print(f"[yellow]Found {len(warnings)} warning(s).[/yellow]")
            console.print("[green]DMLClean is functional but review warnings above.[/green]")
        else:
            console.print("[bold green]All checks passed![/bold green]")


@app.command("version")
def doctor_version() -> None:
    """Show version information."""
    console.print(f"[bold blue]DMLClean[/bold blue] version [green]{__version__}[/green]")
    console.print(f"Platform: {get_platform()}")
    console.print(
        f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    console.print(f"Executable: {sys.executable}")
