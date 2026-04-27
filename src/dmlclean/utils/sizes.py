"""
Human-readable file size utilities for DMLClean.
"""

from __future__ import annotations


def humanize_size(size_bytes: int | float) -> str:
    """
    Convert bytes to human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        str: Human-readable size (e.g., "1.5 GB").
    """
    if size_bytes < 0:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(size_bytes) < 1024.0:
            if unit == "B":
                return f"{int(size_bytes)} {unit}"
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.2f} EB"


def parse_size(size_str: str) -> int:
    """
    Parse a human-readable size string to bytes.

    Args:
        size_str: Size string (e.g., "1.5GB", "500 MB", "100KB").

    Returns:
        int: Size in bytes.

    Raises:
        ValueError: If size string is invalid.
    """
    size_str = size_str.strip().upper()

    units = {
        "B": 1,
        "KB": 1024,
        "K": 1024,
        "MB": 1024**2,
        "M": 1024**2,
        "GB": 1024**3,
        "G": 1024**3,
        "TB": 1024**4,
        "T": 1024**4,
        "PB": 1024**5,
        "P": 1024**5,
    }

    # Try to parse number and unit
    import re

    match = re.match(r"^([\d.]+)\s*([A-Z]*)$", size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    value_str, unit = match.groups()

    try:
        value = float(value_str)
    except ValueError:
        raise ValueError(f"Invalid numeric value: {value_str}") from None

    if not unit:
        unit = "B"

    if unit not in units:
        raise ValueError(f"Unknown unit: {unit}")

    return int(value * units[unit])


def format_size_range(min_bytes: int, max_bytes: int) -> str:
    """
    Format a size range for display.

    Args:
        min_bytes: Minimum size in bytes.
        max_bytes: Maximum size in bytes.

    Returns:
        str: Formatted range (e.g., "1.0 MB - 5.0 MB").
    """
    if min_bytes == max_bytes:
        return humanize_size(min_bytes)
    return f"{humanize_size(min_bytes)} - {humanize_size(max_bytes)}"


def calculate_percentage(part: int, total: int) -> float:
    """
    Calculate percentage of part relative to total.

    Args:
        part: Part value.
        total: Total value.

    Returns:
        float: Percentage (0-100).
    """
    if total == 0:
        return 0.0
    return (part / total) * 100.0
