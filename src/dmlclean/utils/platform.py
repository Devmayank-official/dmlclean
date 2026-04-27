"""
Platform detection and utilities for DMLClean.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from loguru import logger


def get_platform() -> str:
    """
    Get the current platform name.

    Returns:
        str: Platform name ('windows', 'macos', 'linux').
    """
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def is_windows() -> bool:
    """
    Check if running on Windows.

    Returns:
        bool: True if on Windows.
    """
    return sys.platform == "win32"


def is_macos() -> bool:
    """
    Check if running on macOS.

    Returns:
        bool: True if on macOS.
    """
    return sys.platform == "darwin"


def is_linux() -> bool:
    """
    Check if running on Linux.

    Returns:
        bool: True if on Linux.
    """
    return sys.platform.startswith("linux")


def expand_windows_env(path_str: str) -> str:
    """
    Expand Windows environment variables in a path string.

    Handles:
    - %VAR% syntax (Windows-style)
    - $VAR syntax (Unix-style, also works on Windows)
    - ~ (home directory)

    Args:
        path_str: Path string with environment variables.

    Returns:
        str: Expanded path string.
    """
    import re

    # Expand %VAR% syntax (Windows)
    def replace_windows_env(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    path_str = re.sub(r"%([^%]+)%", replace_windows_env, path_str)

    # Expand $VAR syntax (Unix/Windows)
    path_str = os.path.expandvars(path_str)

    # Expand tilde using Path method
    path_str = str(Path(path_str).expanduser())

    logger.debug(f"Expanded Windows env: {path_str}")
    return path_str


def get_system_drive() -> Path:
    """
    Get the system drive (Windows) or root (Unix).

    Returns:
        Path: System drive/root path.
    """
    if is_windows():
        return Path(os.environ.get("SYSTEMDRIVE", "C:"))
    return Path("/")


def get_user_home() -> Path:
    """
    Get the user's home directory.

    Returns:
        Path: Home directory path.
    """
    return Path.home()


def is_admin() -> bool:
    """
    Check if running with administrator/root privileges.

    Returns:
        bool: True if running as admin/root.
    """
    if is_windows():
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore
        except Exception:
            return False
    else:
        return os.geteuid() == 0  # type: ignore


def get_path_separator() -> str:
    """
    Get the platform-specific path separator.

    Returns:
        str: Path separator ('\\' on Windows, '/' on Unix).
    """
    return os.sep


def get_pathsep() -> str:
    """
    Get the platform-specific PATH separator.

    Returns:
        str: PATH separator (';' on Windows, ':' on Unix).
    """
    return os.pathsep


def is_case_sensitive() -> bool:
    """
    Check if the filesystem is case-sensitive.

    Returns:
        bool: True if case-sensitive.
    """
    # Windows and macOS are case-insensitive by default
    return not (is_windows() or is_macos())


def normalize_line_endings(text: str) -> str:
    """
    Normalize line endings to Unix style (LF).

    Args:
        text: Text to normalize.

    Returns:
        str: Text with Unix line endings.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def get_native_line_ending() -> str:
    """
    Get the native line ending for the current platform.

    Returns:
        str: Line ending ('\\r\\n' on Windows, '\\n' on Unix).
    """
    if is_windows():
        return "\r\n"
    return "\n"
