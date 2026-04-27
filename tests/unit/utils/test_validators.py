# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for input validators.

Comprehensive test coverage for security validation functions.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from dmlclean.utils.validators import (
    ValidationError,
    sanitize_string,
    validate_age_days,
    validate_cron_expression,
    validate_file_size,
    validate_limit,
    validate_path,
    validate_profile_name,
)


class TestValidatePath:
    """Test path validation."""

    def test_valid_path(self) -> None:
        """Test valid path passes validation."""
        with TemporaryDirectory() as tmpdir:
            result = validate_path(tmpdir, must_exist=True)
            assert result.exists()
            assert result.is_absolute()

    def test_empty_path_raises(self) -> None:
        """Test empty path raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_path("")

    def test_null_byte_raises(self) -> None:
        """Test null bytes raise ValidationError."""
        with pytest.raises(ValidationError, match="null bytes"):
            validate_path("/tmp\x00/test")

    def test_nonexistent_path_raises(self) -> None:
        """Test non-existent path raises when must_exist=True."""
        with pytest.raises(ValidationError, match="does not exist"):
            validate_path("/nonexistent/path/12345", must_exist=True)

    def test_path_traversal_blocked(self) -> None:
        """Test path traversal is blocked."""
        with pytest.raises(ValidationError):
            validate_path("../../../etc/passwd", must_exist=True)

    def test_valid_relative_path(self) -> None:
        """Test valid relative path is resolved."""
        result = validate_path(".")
        assert result.is_absolute()

    def test_allowed_roots(self) -> None:
        """Test allowed roots restriction."""
        with TemporaryDirectory() as tmpdir:
            allowed = [Path(tmpdir)]
            # Should work - inside allowed root
            result = validate_path(tmpdir, allowed_roots=allowed)
            assert result.exists()

            # Should fail - outside allowed root
            with pytest.raises(ValidationError, match="allowed roots"):
                validate_path("/etc", allowed_roots=allowed)


class TestValidateCronExpression:
    """Test cron expression validation."""

    def test_valid_cron(self) -> None:
        """Test valid cron expression passes."""
        result = validate_cron_expression("0 3 * * *")
        assert result == "0 3 * * *"

    def test_empty_cron_raises(self) -> None:
        """Test empty cron raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_cron_expression("")

    def test_shell_injection_blocked(self) -> None:
        """Test shell injection characters are blocked."""
        dangerous = [";", "|", "&", "$", "`", "(", ")", "<", ">"]
        for char in dangerous:
            with pytest.raises(ValidationError, match="dangerous character"):
                validate_cron_expression(f"0 3 * * * {char} rm -rf /")

    def test_invalid_cron_format(self) -> None:
        """Test invalid cron format raises."""
        with pytest.raises(ValidationError, match="Invalid cron"):
            validate_cron_expression("invalid cron expression")


class TestValidateFileSize:
    """Test file size validation."""

    def test_valid_size(self) -> None:
        """Test valid size passes."""
        result = validate_file_size(100)
        assert result == 100

    def test_zero_size(self) -> None:
        """Test zero size passes."""
        result = validate_file_size(0)
        assert result == 0

    def test_negative_size_raises(self) -> None:
        """Test negative size raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be negative"):
            validate_file_size(-1)

    def test_exceeds_max_raises(self) -> None:
        """Test size exceeding max raises ValidationError."""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_file_size(20000, max_mb=10000)

    def test_string_converted(self) -> None:
        """Test string size is converted to int."""
        result = validate_file_size("100")  # type: ignore
        assert result == 100


class TestValidateAgeDays:
    """Test age validation."""

    def test_valid_age(self) -> None:
        """Test valid age passes."""
        result = validate_age_days(30)
        assert result == 30

    def test_zero_age(self) -> None:
        """Test zero age passes."""
        result = validate_age_days(0)
        assert result == 0

    def test_negative_age_raises(self) -> None:
        """Test negative age raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be negative"):
            validate_age_days(-1)

    def test_exceeds_max_raises(self) -> None:
        """Test age exceeding max raises ValidationError."""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_age_days(5000, max_days=3650)


class TestValidateLimit:
    """Test limit validation."""

    def test_valid_limit(self) -> None:
        """Test valid limit passes."""
        result = validate_limit(50)
        assert result == 50

    def test_below_min_raises(self) -> None:
        """Test limit below min raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be less than"):
            validate_limit(0, min_val=1)

    def test_exceeds_max_raises(self) -> None:
        """Test limit exceeding max raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot exceed"):
            validate_limit(2000, max_val=1000)


class TestSanitizeString:
    """Test string sanitization."""

    def test_valid_string(self) -> None:
        """Test valid string passes."""
        result = sanitize_string("hello world")
        assert result == "hello world"

    def test_whitespace_stripped(self) -> None:
        """Test whitespace is stripped."""
        result = sanitize_string("  hello world  ")
        assert result == "hello world"

    def test_null_bytes_removed(self) -> None:
        """Test null bytes are removed."""
        result = sanitize_string("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_empty_raises(self) -> None:
        """Test empty string raises when allow_empty=False."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            sanitize_string("")

    def test_empty_allowed(self) -> None:
        """Test empty string passes when allow_empty=True."""
        result = sanitize_string("", allow_empty=True)
        assert result == ""

    def test_exceeds_max_length_raises(self) -> None:
        """Test string exceeding max length raises."""
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            sanitize_string("a" * 2000, max_length=1000)


class TestValidateProfileName:
    """Test profile name validation."""

    def test_valid_name(self) -> None:
        """Test valid profile name passes."""
        result = validate_profile_name("developer")
        assert result == "developer"

    def test_name_with_underscore(self) -> None:
        """Test name with underscore passes."""
        result = validate_profile_name("my_profile")
        assert result == "my_profile"

    def test_name_with_hyphen(self) -> None:
        """Test name with hyphen passes."""
        result = validate_profile_name("my-profile")
        assert result == "my-profile"

    def test_empty_raises(self) -> None:
        """Test empty name raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_profile_name("")

    def test_invalid_characters_raises(self) -> None:
        """Test invalid characters raise ValidationError."""
        with pytest.raises(ValidationError, match="only contain"):
            validate_profile_name("my@profile!")

    def test_too_long_raises(self) -> None:
        """Test name too long raises ValidationError."""
        with pytest.raises(ValidationError, match="too long"):
            validate_profile_name("a" * 100)


__all__ = [
    "TestSanitizeString",
    "TestValidateAgeDays",
    "TestValidateCronExpression",
    "TestValidateFileSize",
    "TestValidateLimit",
    "TestValidatePath",
    "TestValidateProfileName",
]
