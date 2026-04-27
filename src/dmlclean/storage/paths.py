r"""
Path utilities for DMLClean storage.

Provides cross-platform path resolution for DML Labs/DML Clean directory structure.

Storage Paths (Cross-Platform):
    Windows: C:\Users\%USERNAME%\DML Labs\DML Clean\
    macOS:   /Users/%USERNAME%/DML Labs/DML Clean/
    Linux:   /home/%USERNAME%/DML Labs/DML Clean/

All paths use Path.home() for cross-platform compatibility.
NO hardcoded paths - uses unified constants from dmlclean.constants.app.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from loguru import logger

from dmlclean.constants.app import (
    STORAGE_BASE,
    STORAGE_CACHE,
    STORAGE_CONFIG,
    STORAGE_DATA,
    STORAGE_HISTORY,
    STORAGE_LOGS,
)


@lru_cache(maxsize=1)
def get_base_dir() -> Path:
    """
    Get the base directory for DMLClean storage.

    Returns:
        Path: Base directory path.
            - Windows: C:\\Users\\<username>\\DML Labs\\DML Clean
            - macOS:   /Users/<username>/DML Labs/DML Clean
            - Linux:   /home/<username>/DML Labs/DML Clean
    """
    # Use unified constant from constants/app.py
    base = STORAGE_BASE
    logger.debug(f"DMLClean base directory: {base}")
    return base


def get_config_dir() -> Path:
    """
    Get the configuration directory.

    Returns:
        Path: Configuration directory (<base>/config).
    """
    return get_base_dir() / STORAGE_CONFIG


def get_profiles_dir() -> Path:
    """
    Get the profiles directory.

    Returns:
        Path: Profiles directory (<base>/config/profiles).
    """
    return get_config_dir() / "profiles"


def get_data_dir() -> Path:
    """
    Get the data directory for databases and state files.

    Returns:
        Path: Data directory (<base>/data).
    """
    return get_base_dir() / STORAGE_DATA


def get_migrations_dir() -> Path:
    """
    Get the database migrations directory.

    Returns:
        Path: Migrations directory (src/dmlclean/storage/migrations).

    Note:
        Uses multiple fallback strategies to find migrations:
        1. Try package-relative path (works in most cases)
        2. Try absolute path from project root (development)
        3. Try importlib.resources (Python 3.9+ packaged)
    """
    from loguru import logger

    # Strategy 1: Try package-relative path using __file__
    try:
        import dmlclean.storage

        pkg_path = Path(dmlclean.storage.__file__).parent / "migrations"
        if pkg_path.exists():
            logger.debug(f"Migrations dir (package): {pkg_path}")
            return pkg_path
    except Exception as e:
        logger.warning(f"Strategy 1 (package path) failed: {e}")

    # Strategy 2: Try absolute path from project root (development mode)
    try:
        # Go up from paths.py: storage/paths.py → storage → dmlclean → src → project_root
        current_file = Path(__file__).resolve()
        dev_path = (
            current_file.parent.parent.parent.parent / "src" / "dmlclean" / "storage" / "migrations"
        )
        if dev_path.exists():
            logger.debug(f"Migrations dir (development): {dev_path}")
            return dev_path
    except Exception as e:
        logger.warning(f"Strategy 2 (development path) failed: {e}")

    # Strategy 3: Try importlib.resources (for packaged installations)
    try:
        from importlib.resources import files

        resource_path = Path(str(files("dmlclean.storage.migrations")))
        if resource_path.exists():
            logger.debug(f"Migrations dir (importlib): {resource_path}")
            return resource_path
    except Exception as e:
        logger.warning(f"Strategy 3 (importlib.resources) failed: {e}")

    # Fallback: Return package path even if doesn't exist (will cause clear error later)
    import dmlclean.storage

    fallback_path = Path(dmlclean.storage.__file__).parent / "migrations"
    logger.error(f"Migrations directory not found! Fallback path: {fallback_path}")
    return fallback_path


def get_history_dir() -> Path:
    """
    Get the history directory for manifests and reports.

    Returns:
        Path: History directory (<base>/history).
    """
    return get_base_dir() / STORAGE_HISTORY


def get_manifests_dir() -> Path:
    """
    Get the manifests subdirectory.

    Returns:
        Path: Manifests directory (<base>/history/manifests).
    """
    return get_history_dir() / "manifests"


def get_reports_dir() -> Path:
    """
    Get the reports subdirectory.

    Returns:
        Path: Reports directory (<base>/history/reports).
    """
    return get_history_dir() / "reports"


def get_logs_dir() -> Path:
    """
    Get the logs directory.

    Returns:
        Path: Logs directory (<base>/logs).
    """
    return get_base_dir() / STORAGE_LOGS


def get_cache_dir() -> Path:
    """
    Get the cache directory.

    Returns:
        Path: Cache directory (<base>/cache).
    """
    return get_base_dir() / STORAGE_CACHE


def get_temp_dir() -> Path:
    """
    Get the temporary files directory.

    Returns:
        Path: Temp directory (<base>/cache/temp).
    """
    return get_cache_dir() / "temp"


def get_db_path() -> Path:
    """
    Get the SQLite database file path.

    Returns:
        Path: Database file path (<base>/data/dml_clean.db).
    """
    return get_data_dir() / "dml_clean.db"


def get_config_path() -> Path:
    """
    Get the main configuration file path.

    Returns:
        Path: Config file path (<base>/config/config.toml).
    """
    return get_config_dir() / "config.toml"


def get_log_path() -> Path:
    """
    Get the main log file path.

    Returns:
        Path: Log file path (<base>/logs/dml_clean.log).
    """
    return get_logs_dir() / "dml_clean.log"


def get_state_path() -> Path:
    """
    Get the incremental scan state file path.

    Returns:
        Path: State file path (<base>/data/state.json).
    """
    return get_data_dir() / "state.json"


def ensure_all_dirs() -> None:
    """
    Create the entire DML Labs/DML Clean directory structure.

    Creates all required directories with proper permissions:
    - Config directory: 0o700 on Unix (secure)
    - All other directories: standard permissions

    This should be called on first run to ensure all paths exist.
    """
    dirs = [
        get_base_dir(),
        get_config_dir(),
        get_profiles_dir(),
        get_data_dir(),
        get_migrations_dir(),
        get_history_dir(),
        get_manifests_dir(),
        get_reports_dir(),
        get_logs_dir(),
        get_cache_dir(),
        get_temp_dir(),
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {d}")

    # Secure config directory permissions on Unix (not Windows)
    if os.name != "nt":
        try:
            get_config_dir().chmod(0o700)
            logger.debug(f"Set config directory permissions to 0o700: {get_config_dir()}")
        except OSError as e:
            logger.warning(f"Failed to set config directory permissions: {e}")

    logger.info(f"DMLClean directory structure ensured at: {get_base_dir()}")


def get_storage_info() -> dict[str, str]:
    """
    Get all storage paths as a dictionary.

    Returns:
        dict[str, str]: Mapping of path name to absolute path.
    """
    return {
        "base_dir": str(get_base_dir()),
        "config_dir": str(get_config_dir()),
        "profiles_dir": str(get_profiles_dir()),
        "data_dir": str(get_data_dir()),
        "migrations_dir": str(get_migrations_dir()),
        "history_dir": str(get_history_dir()),
        "manifests_dir": str(get_manifests_dir()),
        "reports_dir": str(get_reports_dir()),
        "logs_dir": str(get_logs_dir()),
        "cache_dir": str(get_cache_dir()),
        "temp_dir": str(get_temp_dir()),
        "db_path": str(get_db_path()),
        "config_path": str(get_config_path()),
        "log_path": str(get_log_path()),
        "state_path": str(get_state_path()),
    }
