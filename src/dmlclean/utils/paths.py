"""
Path utilities for DMLClean.

Provides path expansion, normalization, and platform-specific helpers.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from loguru import logger


def expand_path(path_str: str) -> Path:
    """
    Expand a path string to a full Path object.

    Handles:
    - Environment variables (%VAR% on Windows, $VAR on Unix)
    - Tilde expansion (~ to home directory)
    - Relative to absolute path conversion

    Args:
        path_str: Path string to expand.

    Returns:
        Path: Expanded absolute path.
    """
    if not path_str:
        raise ValueError("Path string cannot be empty")

    # Expand environment variables
    expanded = os.path.expandvars(path_str)

    # Expand tilde using Path method
    expanded = str(Path(expanded).expanduser())

    # Convert to Path and resolve to absolute
    path = Path(expanded).resolve()

    logger.debug(f"Expanded path: {path_str} -> {path}")
    return path


def normalize_path(path: Path | str) -> Path:
    """
    Normalize a path for consistent comparison.

    - Resolves to absolute path
    - Normalizes case on case-insensitive filesystems
    - Removes redundant separators and up-level references

    Args:
        path: Path to normalize.

    Returns:
        Path: Normalized path.
    """
    if isinstance(path, str):
        path = Path(path)

    # Resolve to absolute path
    normalized = path.resolve()

    # On Windows and macOS, normalize case
    if os.name == "nt" or os.uname().sysname == "Darwin":  # type: ignore
        normalized = Path(str(normalized).lower())

    return normalized


def is_subpath_of(child: Path, parent: Path) -> bool:
    """
    Check if a path is a subpath of another path.

    Args:
        child: Potential child path.
        parent: Potential parent path.

    Returns:
        bool: True if child is a subpath of parent.
    """
    try:
        child_resolved = child.resolve()
        parent_resolved = parent.resolve()
        child_resolved.relative_to(parent_resolved)
        return True
    except ValueError:
        return False


def safe_expand_path(path_str: str, default: Path | None = None) -> Path | None:
    """
    Safely expand a path, returning default if expansion fails.

    Args:
        path_str: Path string to expand.
        default: Default value if expansion fails.

    Returns:
        Path | None: Expanded path or default.
    """
    try:
        return expand_path(path_str)
    except (ValueError, OSError):
        return default


def get_temp_dir() -> Path:
    """
    Get the system temporary directory.

    Returns:
        Path: System temp directory.
    """
    return Path(tempfile.gettempdir()).resolve()


def ensure_absolute(path: Path | str, base: Path | None = None) -> Path:
    """
    Ensure a path is absolute, using base if relative.

    Args:
        path: Path to check.
        base: Base directory for relative paths (default: cwd).

    Returns:
        Path: Absolute path.
    """
    if isinstance(path, str):
        path = Path(path)

    if path.is_absolute():
        return path.resolve()

    if base is None:
        base = Path.cwd()

    return (base / path).resolve()
