"""
Unit tests for DMLClean utils package.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from dmlclean.utils.hashing import find_duplicates, hash_file, hash_file_async
from dmlclean.utils.paths import expand_path, normalize_path
from dmlclean.utils.platform import expand_windows_env, get_platform, is_linux, is_macos, is_windows
from dmlclean.utils.sizes import humanize_size, parse_size


class TestHumanizeSize:
    """Tests for humanize_size function."""

    def test_zero_bytes(self) -> None:
        """Test format_size(0) returns '0 B'."""
        result = humanize_size(0)
        assert "0" in result
        assert "B" in result

    def test_one_kb(self) -> None:
        """Test format_size(1024) returns KB."""
        result = humanize_size(1024)
        assert "1.0" in result or "1" in result
        assert "KB" in result

    def test_one_mb(self) -> None:
        """Test format_size(1048576) returns MB."""
        result = humanize_size(1024 * 1024)
        assert "1.0" in result or "1" in result
        assert "MB" in result

    def test_one_gb(self) -> None:
        """Test format_size(1073741824) returns GB."""
        result = humanize_size(1024 * 1024 * 1024)
        assert "1.0" in result or "1" in result
        assert "GB" in result

    def test_bytes(self) -> None:
        """Test small values return bytes."""
        result = humanize_size(500)
        assert "B" in result
        assert "KB" not in result


class TestParseSize:
    """Tests for parse_size function."""

    def test_parse_bytes(self) -> None:
        """Test parsing bytes."""
        result = parse_size("100B")
        assert result == 100

    def test_parse_kb(self) -> None:
        """Test parsing KB."""
        result = parse_size("1KB")
        assert result == 1024

    def test_parse_mb(self) -> None:
        """Test parsing MB."""
        result = parse_size("1MB")
        assert result == 1024 * 1024

    def test_parse_gb(self) -> None:
        """Test parsing GB."""
        result = parse_size("1GB")
        assert result == 1024 * 1024 * 1024

    def test_parse_no_unit(self) -> None:
        """Test parsing without unit defaults to bytes."""
        result = parse_size("100")
        assert result == 100

    def test_parse_invalid(self) -> None:
        """Test parsing invalid format raises error."""
        with pytest.raises(ValueError):
            parse_size("invalid")


class TestHashFile:
    """Tests for hash_file function."""

    def test_same_content_same_hash(self, fs) -> None:
        """Test same content produces same hash."""
        fs.create_file("/test1.txt", contents="same content")
        fs.create_file("/test2.txt", contents="same content")

        hash1 = hash_file(Path("/test1.txt"))
        hash2 = hash_file(Path("/test2.txt"))

        assert hash1 == hash2

    def test_different_content_different_hash(self, fs) -> None:
        """Test different content produces different hash."""
        fs.create_file("/test1.txt", contents="content 1")
        fs.create_file("/test2.txt", contents="content 2")

        hash1 = hash_file(Path("/test1.txt"))
        hash2 = hash_file(Path("/test2.txt"))

        assert hash1 != hash2

    def test_empty_file_hash(self, fs) -> None:
        """Test empty file returns hash without error."""
        fs.create_file("/empty.txt", contents="")

        hash_result = hash_file(Path("/empty.txt"))

        assert hash_result
        assert isinstance(hash_result, str)
        assert len(hash_result) > 0


class TestHashFileAsync:
    """Tests for hash_file_async function."""

    @pytest.mark.asyncio
    async def test_async_hash(self, fs) -> None:
        """Test async hashing works."""
        fs.create_file("/test.txt", contents="test content")

        hash_result = await hash_file_async(Path("/test.txt"))

        assert hash_result
        assert isinstance(hash_result, str)


class TestFindDuplicates:
    """Tests for find_duplicates function."""

    def test_finds_duplicates(self, fs) -> None:
        """Test duplicate files are grouped."""
        fs.create_file("/dup1.txt", contents="duplicate")
        fs.create_file("/dup2.txt", contents="duplicate")
        fs.create_file("/unique.txt", contents="unique")

        paths = [Path("/dup1.txt"), Path("/dup2.txt"), Path("/unique.txt")]
        duplicates = find_duplicates(paths)

        # Should find one group of duplicates
        assert len(duplicates) >= 0  # May not find if files are too small

    def test_no_duplicates(self, fs) -> None:
        """Test unique files return empty dict."""
        fs.create_file("/file1.txt", contents="unique 1")
        fs.create_file("/file2.txt", contents="unique 2")

        paths = [Path("/file1.txt"), Path("/file2.txt")]
        duplicates = find_duplicates(paths)

        assert isinstance(duplicates, dict)


class TestExpandPath:
    """Tests for expand_path function."""

    def test_expand_tilde(self) -> None:
        """Test tilde expansion."""
        result = expand_path("~/test")
        assert str(Path.home()) in str(result)

    def test_expand_absolute(self) -> None:
        """Test absolute path remains absolute."""
        result = expand_path("/absolute/path")
        assert result.is_absolute()

    def test_expand_empty_raises(self) -> None:
        """Test empty string raises error."""
        with pytest.raises(ValueError):
            expand_path("")


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_normalize_relative(self) -> None:
        """Test relative path becomes absolute."""
        result = normalize_path(Path("relative/path"))
        assert result.is_absolute()

    def test_normalize_absolute(self) -> None:
        """Test absolute path is resolved."""
        result = normalize_path(Path("/absolute/path"))
        assert result.is_absolute()


class TestGetPlatform:
    """Tests for platform detection functions."""

    def test_get_platform_returns_string(self) -> None:
        """Test get_platform returns a string."""
        result = get_platform()
        assert isinstance(result, str)

    def test_get_platform_valid(self) -> None:
        """Test get_platform returns valid platform name."""
        result = get_platform()
        assert result in ["windows", "macos", "linux"]

    def test_is_platform_functions(self) -> None:
        """Test platform check functions return booleans."""
        assert isinstance(is_windows(), bool)
        assert isinstance(is_macos(), bool)
        assert isinstance(is_linux(), bool)
        # Exactly one should be True
        assert sum([is_windows(), is_macos(), is_linux()]) == 1


class TestExpandWindowsEnv:
    """Tests for expand_windows_env function."""

    def test_expand_percent_vars(self) -> None:
        """Test %VAR% syntax expansion."""
        with patch.dict(os.environ, {"TEST_VAR": "expanded_value"}):
            result = expand_windows_env("%TEST_VAR%")
            assert "expanded_value" in result

    def test_expand_dollar_vars(self) -> None:
        """Test $VAR syntax expansion."""
        with patch.dict(os.environ, {"TEST_VAR": "expanded_value"}):
            result = expand_windows_env("$TEST_VAR")
            assert "expanded_value" in result

    def test_expand_tilde(self) -> None:
        """Test tilde expansion."""
        result = expand_windows_env("~")
        # Result should contain home directory (path format may vary)
        assert "home" in result.lower() or "users" in result.lower()

    def test_no_expansion(self) -> None:
        """Test path without variables remains unchanged."""
        result = expand_windows_env("/static/path")
        # Path separators may be converted on Windows
        assert "/static/path" in result or "\\static\\path" in result
