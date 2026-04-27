"""
Utility modules for DMLClean.

This package provides:
- Path helpers (platformdirs integration, XDG compliance)
- Human-readable file sizes
- xxhash file fingerprinting
- Platform detection and Windows environment variable expansion
- Date and time utilities
"""

from dmlclean.utils.dates import (
    calculate_age_days,
    datetime_to_iso,
    format_date,
    format_datetime_relative,
    get_cron_human_readable,
    get_date_range,
    get_timestamp,
    iso_to_datetime,
    parse_date,
    parse_natural_language_schedule,
    timestamp_to_datetime,
    truncate_to_date,
)
from dmlclean.utils.hashing import hash_file, hash_file_async
from dmlclean.utils.paths import expand_path, normalize_path
from dmlclean.utils.platform import get_platform, is_linux, is_macos, is_windows
from dmlclean.utils.sizes import humanize_size, parse_size

__all__ = [
    # Dates
    "calculate_age_days",
    "datetime_to_iso",
    "expand_path",
    "format_date",
    "format_datetime_relative",
    "get_cron_human_readable",
    "get_date_range",
    "get_platform",
    "get_timestamp",
    "hash_file",
    "hash_file_async",
    "humanize_size",
    "is_linux",
    "is_macos",
    "is_windows",
    "iso_to_datetime",
    "normalize_path",
    "parse_date",
    "parse_natural_language_schedule",
    "parse_size",
    "timestamp_to_datetime",
    "truncate_to_date",
]
