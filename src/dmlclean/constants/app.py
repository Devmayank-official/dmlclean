"""
Application metadata constants for DMLClean.

These constants define the app's identity and storage configuration.
"""

from pathlib import Path

# Application identity
APP_NAME: str = "DMLClean"
"""Human-readable application name."""

APP_BINARY: str = "dmlclean"
"""Command-line binary name (used in pipx/pip installs)."""

APP_VERSION: str = "0.1.0"
"""Current application version (semantic versioning)."""

# Storage configuration - UNIFIED PATHS
# All storage uses Path.home() for cross-platform compatibility
STORAGE_ORG: str = "DML Labs"
"""Organization name for storage paths."""

STORAGE_APP: str = "DML Clean"
"""Application name for storage paths."""

# Unified base path - single source of truth
# All DMLClean data is stored under: ~/DML Labs/DML Clean/
STORAGE_BASE: Path = Path.home() / STORAGE_ORG / STORAGE_APP
"""
Unified base storage directory.

All DMLClean data is stored under this directory:
- Windows: C:\\Users\\<username>\\DML Labs\\DML Clean\\
- macOS:   /Users/<username>/DML Labs/DML Clean/
- Linux:   /home/<username>/DML Labs/DML Clean/
"""

# Subdirectory constants
STORAGE_CONFIG: str = "config"
STORAGE_DATA: str = "data"
STORAGE_HISTORY: str = "history"
STORAGE_LOGS: str = "logs"
STORAGE_CACHE: str = "cache"
STORAGE_MANIFESTS: str = "history/manifests"
STORAGE_REPORTS: str = "history/reports"

# Python version requirements
MIN_PYTHON: tuple[int, int] = (3, 11)
"""Minimum required Python version (major, minor)."""
