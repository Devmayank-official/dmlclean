"""
Format and mode constants for DMLClean.

Defines supported output formats, scan modes, and clean modes.
"""

# Supported output formats for reports and exports
SUPPORTED_OUTPUT_FORMATS: list[str] = [
    "terminal",
    "json",
    "csv",
    "html",
]
"""List of supported output formats for reports and exports."""

# Supported scan modes
SUPPORTED_SCAN_MODES: list[str] = [
    "fast",
    "deep",
    "custom",
]
"""
List of supported scan modes:
- fast: Pre-defined high-confidence paths only (<5 seconds)
- deep: Full recursive traversal with duplicate detection (30s-5min)
- custom: User-defined paths and patterns from config profile
"""

# Supported clean modes
SUPPORTED_CLEAN_MODES: list[str] = [
    "dry-run",
    "trash",
    "permanent",
]
"""
List of supported clean modes:
- dry-run: Calculate and display what would be deleted (default, zero writes)
- trash: Move files to OS Trash via Send2Trash (supports undo)
- permanent: Hard delete via shutil (requires --force, no undo)
"""

# Supported date formats for CLI parsing
DATE_FORMATS: list[str] = [
    "%Y-%m-%d",  # ISO date: 2025-01-01
    "%d/%m/%Y",  # EU date: 01/01/2025
    "%Y-%m-%dT%H:%M:%S",  # ISO datetime: 2025-01-01T00:00:00
    "%Y-%m-%d %H:%M:%S",  # Human datetime: 2025-01-01 00:00:00
]
"""List of supported date formats for CLI --since/--until flags."""

# Relative date keywords for natural language parsing
RELATIVE_DATE_KEYWORDS: dict[str, int] = {
    "today": 0,
    "yesterday": 1,
    "last_week": 7,
    "last_month": 30,
    "last_year": 365,
}
"""Mapping of relative date keywords to days ago."""
