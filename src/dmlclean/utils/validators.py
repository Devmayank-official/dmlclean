# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Input validation utilities for DMLClean.

Provides security-focused validation for:
- File paths (prevent path traversal)
- Cron expressions (prevent injection)
- File sizes and ages (prevent abuse)
- User input sanitization
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str | None = None, value: Any | None = None) -> None:
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


def validate_path(
    path: str | Path,
    must_exist: bool = False,
    must_be_absolute: bool = False,
    allowed_roots: list[Path] | None = None,
) -> Path:
    """
    Validate and sanitize a file path.

    Security checks:
    1. Prevent path traversal (../ or ..\\)
    2. Prevent null bytes and invalid characters
    3. Optionally verify path exists
    4. Optionally restrict to allowed root directories

    Args:
        path: Path to validate.
        must_exist: Whether path must exist.
        must_be_absolute: Whether path must be absolute.
        allowed_roots: List of allowed root directories.

    Returns:
        Path: Validated and resolved path.

    Raises:
        ValidationError: If path is invalid.

    Example:
        ```python
        # Validate user-provided path
        safe_path = validate_path(user_input, must_exist=True)

        # Validate with allowed roots
        safe_path = validate_path(
            user_input,
            allowed_roots=[Path.home(), Path("/tmp")]
        )
        ```
    """
    if not path:
        raise ValidationError("Path cannot be empty", field="path", value=path)

    path_str = str(path).strip()

    # Check for null bytes
    if "\x00" in path_str:
        raise ValidationError("Path contains null bytes", field="path", value=path_str)

    # Check for path traversal attempts
    if ".." in path_str:
        # Allow .. only if it resolves safely
        try:
            path_obj = Path(path_str).resolve()
            # Verify resolved path doesn't escape expected roots
            if allowed_roots:
                if not any(str(path_obj).startswith(str(r)) for r in allowed_roots):
                    raise ValidationError(
                        "Path resolves outside allowed roots",
                        field="path",
                        value=path_str,
                    )
        except Exception as e:
            raise ValidationError(f"Invalid path traversal: {e}", field="path", value=path_str)
    else:
        path_obj = Path(path_str)

    # Resolve to absolute path
    try:
        path_obj = path_obj.resolve()
    except Exception as e:
        raise ValidationError(f"Cannot resolve path: {e}", field="path", value=path_str)

    # Check if absolute
    if must_be_absolute and not path_obj.is_absolute():
        raise ValidationError("Path must be absolute", field="path", value=path_str)

    # Check if exists
    if must_exist and not path_obj.exists():
        raise ValidationError(f"Path does not exist: {path_obj}", field="path", value=path_str)

    # Check against allowed roots
    if allowed_roots:
        if not any(str(path_obj).startswith(str(r)) for r in allowed_roots):
            raise ValidationError(
                "Path not in allowed roots",
                field="path",
                value=path_str,
            )

    return path_obj


def validate_cron_expression(expr: str) -> str:
    """
    Validate cron expression syntax.

    Security checks:
    1. Valid cron format (5 or 7 fields)
    2. No shell injection characters
    3. Reasonable numeric ranges

    Args:
        expr: Cron expression to validate.

    Returns:
        str: Validated cron expression.

    Raises:
        ValidationError: If expression is invalid.

    Example:
        ```python
        # Validate cron expression
        safe_cron = validate_cron_expression("0 3 * * *")
        ```
    """
    if not expr or not expr.strip():
        raise ValidationError("Cron expression cannot be empty", field="cron_expression")

    expr = expr.strip()

    # Check for shell injection characters
    dangerous_chars = [";", "|", "&", "$", "`", "(", ")", "<", ">", "\\", "\n", "\r"]
    for char in dangerous_chars:
        if char in expr:
            raise ValidationError(
                f"Cron expression contains dangerous character: {char}",
                field="cron_expression",
                value=expr,
            )

    # Validate format using croniter if available
    try:
        from croniter import croniter

        croniter(expr)
    except ImportError:
        # Fallback: basic validation
        parts = expr.split()
        if len(parts) not in (5, 6, 7):
            raise ValidationError(
                f"Cron expression must have 5-7 fields, got {len(parts)}",
                field="cron_expression",
                value=expr,
            )
    except Exception as e:
        raise ValidationError(f"Invalid cron expression: {e}", field="cron_expression", value=expr)

    return expr


def validate_file_size(size_mb: int, max_mb: int = 10000) -> int:
    """
    Validate file size parameter.

    Args:
        size_mb: Size in MB to validate.
        max_mb: Maximum allowed size (default 10GB).

    Returns:
        int: Validated size.

    Raises:
        ValidationError: If size is invalid.
    """
    if not isinstance(size_mb, int):
        try:
            size_mb = int(size_mb)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Size must be an integer, got {type(size_mb).__name__}",
                field="size_mb",
                value=size_mb,
            )

    if size_mb < 0:
        raise ValidationError(f"Size cannot be negative: {size_mb}", field="size_mb", value=size_mb)

    if size_mb > max_mb:
        raise ValidationError(
            f"Size exceeds maximum ({max_mb}MB): {size_mb}",
            field="size_mb",
            value=size_mb,
        )

    return size_mb


def validate_age_days(days: int, max_days: int = 3650) -> int:
    """
    Validate age parameter.

    Args:
        days: Age in days to validate.
        max_days: Maximum allowed days (default 10 years).

    Returns:
        int: Validated age.

    Raises:
        ValidationError: If age is invalid.
    """
    if not isinstance(days, int):
        try:
            days = int(days)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Age must be an integer, got {type(days).__name__}",
                field="age_days",
                value=days,
            )

    if days < 0:
        raise ValidationError(f"Age cannot be negative: {days}", field="age_days", value=days)

    if days > max_days:
        raise ValidationError(
            f"Age exceeds maximum ({max_days} days): {days}",
            field="age_days",
            value=days,
        )

    return days


def validate_limit(limit: int, min_val: int = 1, max_val: int = 1000) -> int:
    """
    Validate limit/pagination parameter.

    Args:
        limit: Limit value to validate.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        int: Validated limit.

    Raises:
        ValidationError: If limit is invalid.
    """
    if not isinstance(limit, int):
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Limit must be an integer, got {type(limit).__name__}",
                field="limit",
                value=limit,
            )

    if limit < min_val:
        raise ValidationError(
            f"Limit cannot be less than {min_val}: {limit}",
            field="limit",
            value=limit,
        )

    if limit > max_val:
        raise ValidationError(
            f"Limit cannot exceed {max_val}: {limit}",
            field="limit",
            value=limit,
        )

    return limit


def sanitize_string(value: str, max_length: int = 1000, allow_empty: bool = False) -> str:
    """
    Sanitize a user-provided string.

    Security checks:
    1. Strip whitespace
    2. Remove null bytes
    3. Enforce maximum length
    4. Optionally prevent empty strings

    Args:
        value: String to sanitize.
        max_length: Maximum allowed length.
        allow_empty: Whether empty strings are allowed.

    Returns:
        str: Sanitized string.

    Raises:
        ValidationError: If string is invalid.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"Value must be a string, got {type(value).__name__}",
            field="value",
            value=value,
        )

    # Strip whitespace
    value = value.strip()

    # Remove null bytes
    value = value.replace("\x00", "")

    # Check empty
    if not value and not allow_empty:
        raise ValidationError("Value cannot be empty", field="value")

    # Check length
    if len(value) > max_length:
        raise ValidationError(
            f"Value exceeds maximum length ({max_length}): {len(value)}",
            field="value",
            value=value[:50] + "...",
        )

    return value


def validate_profile_name(name: str) -> str:
    """
    Validate profile name.

    Args:
        name: Profile name to validate.

    Returns:
        str: Validated profile name.

    Raises:
        ValidationError: If name is invalid.
    """
    if not name:
        raise ValidationError("Profile name cannot be empty", field="profile_name")

    # Only allow alphanumeric, underscore, hyphen
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValidationError(
            "Profile name can only contain letters, numbers, underscore, and hyphen",
            field="profile_name",
            value=name,
        )

    if len(name) > 50:
        raise ValidationError(
            f"Profile name too long (max 50): {len(name)}",
            field="profile_name",
            value=name,
        )

    return name


__all__ = [
    "ValidationError",
    "sanitize_string",
    "validate_age_days",
    "validate_cron_expression",
    "validate_file_size",
    "validate_limit",
    "validate_path",
    "validate_profile_name",
]
