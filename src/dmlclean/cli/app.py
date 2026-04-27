"""
Main entry point for the DML Clean CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from dmlclean import __version__
from dmlclean.container import Container, get_container
from dmlclean.utils.platform import get_platform

# Initialize Rich console
console = Console()

# Global state for container and middleware
_container: Container | None = None
_error_handler = None
_update_check = None


# Create Typer app
app = typer.Typer(
    name="dmlclean",
    help="Enterprise-grade, module-driven framework engineered for automated system maintenance and storage lifecycle management.",
    epilog="Use 'dmlclean [COMMAND] --help' for more information on a command.",
    no_args_is_help=False,
    add_completion=True,
)


def _setup_logging(verbose: bool, quiet: bool) -> None:
    """
    Configure loguru logging based on CLI flags.

    Args:
        verbose: Enable debug logging.
        quiet: Suppress all output except errors.
    """
    from loguru import logger

    from dmlclean.storage.paths import get_logs_dir

    # Remove default handler
    logger.remove()

    # Determine log level
    if quiet:
        level = "ERROR"
    elif verbose:
        level = "DEBUG"
    else:
        # Default for enterprise CLI is WARNING (silence DEBUG/INFO noise)
        level = "WARNING"

    # Add console handler (unless quiet mode)
    if not quiet:
        logger.add(
            sys.stderr,
            level=level,
            format=(
                "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    # Add file handler - use unified storage path
    try:
        log_dir = get_logs_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "dmlclean.log"

        logger.add(
            str(log_file),
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
                "{name}:{function}:{line} - {message}"
            ),
            serialize=False,
        )
        logger.debug(f"Logging to {log_file}")
    except Exception as e:
        logger.warning(f"Failed to setup file logging: {e}")


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from rich.panel import Panel
        
        content = (
            f"[bold blue]DML Clean[/bold blue] v{__version__}\n"
            f"[dim]Enterprise-grade, module-driven framework engineered for automated system maintenance.[/dim]"
        )
        
        console.print(
            Panel(
                content, 
                expand=False, 
                border_style="blue",
                padding=(1, 2)
            )
        )
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_version_callback,
        help="Show version and exit.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable debug logging.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all output except errors.",
    ),
    # ruff: noqa: B008  # typer.Option is the standard way to use Typer
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Override config file location.",
    ),
) -> None:
    """
    DML Clean - Enterprise-grade, module-driven framework engineered for automated system maintenance and storage lifecycle management.

    Orchestrate high-concurrency scans, transactional "Safe-Trash" operations, and 
    automated storage lifecycles with deterministic safety and manifest-based auditing.
    """
    from loguru import logger

    from dmlclean.cli.middleware.error_handler import ErrorHandler
    from dmlclean.cli.middleware.update_check import UpdateCheckMiddleware

    # Setup logging immediately to silence initialization noise
    _setup_logging(verbose, quiet)

    # Only initialize middleware if a command is being run
    if ctx.invoked_subcommand is not None:
        global _container, _error_handler, _update_check

        # Initialize DI Container
        _container = get_container(config_path=config)

        # Register CLI Middleware
        _error_handler = ErrorHandler.register(console, verbose=verbose)
        _update_check = UpdateCheckMiddleware.register(console, check_interval_hours=24)

        logger.debug(f"DML Clean {__version__} started")
        logger.debug(f"Platform: {get_platform()}, Python: {sys.version}")


# Import and register subcommands
# These must be imported after the app is created to avoid circular imports
from dmlclean.cli.commands import (  # noqa: E402
    clean_app,
    config_app,
    doctor_app,
    history_app,
    notification_app,
    protect_app,
    report_app,
    scan_app,
    schedule_app,
)
from dmlclean.cli.commands.plugin_cmd import app as plugin_app  # noqa: E402

# Import and register NEW subcommands
from dmlclean.cli.commands.profile import app as profile_app  # noqa: E402
from dmlclean.cli.commands.storage_cmd import app as storage_app  # noqa: E402
from dmlclean.cli.commands.system import app as system_app  # noqa: E402
from dmlclean.cli.commands.trends import app as trends_app  # noqa: E402

# Register subcommands
app.add_typer(scan_app, name="scan")  # type: ignore[has-type]
app.add_typer(clean_app, name="clean")  # type: ignore[has-type]
app.add_typer(schedule_app, name="schedule")  # type: ignore[has-type]
app.add_typer(config_app, name="config")  # type: ignore[has-type]
app.add_typer(protect_app, name="protect")  # type: ignore[has-type]
app.add_typer(history_app, name="history")  # type: ignore[has-type]
app.add_typer(report_app, name="report")  # type: ignore[has-type]
app.add_typer(doctor_app, name="doctor")  # type: ignore[has-type]
app.add_typer(profile_app, name="profile")  # type: ignore[has-type]
app.add_typer(plugin_app, name="plugin")  # type: ignore[has-type]
app.add_typer(storage_app, name="storage")  # type: ignore[has-type]
app.add_typer(trends_app, name="trends")  # type: ignore[has-type]
app.add_typer(system_app, name="system")  # type: ignore[has-type]
app.add_typer(notification_app, name="notification")  # type: ignore[has-type]


# Top-level version command (alias for system version)
@app.command("version")
def version_cmd() -> None:
    """Show version info in the DML Stream identity card style."""
    from rich.panel import Panel
    from dmlclean import __version__

    content = (
        f"[bold blue]DML Clean[/bold blue] v{__version__}\n"
        f"[dim]Enterprise-Ready Storage Optimization & Lifecycle Orchestrator[/dim]"
    )
    
    console.print(
        Panel(
            content, 
            expand=False, 
            border_style="blue",
            padding=(1, 2)
        )
    )


if __name__ == "__main__":
    app()
