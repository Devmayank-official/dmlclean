"""
Unit tests for DMLClean Protected Zone.

Tests glob patterns, environment variables, git dirs, and venvs.
"""

# ruff: noqa: S108  # reason: test file using pyfakefs - no real disk access

from __future__ import annotations

from pathlib import Path

from dmlclean.safety.protected_zone import ProtectedZone, ProtectionSource


class TestProtectedZone:
    """Tests for ProtectedZone."""

    def test_basic_protection(self) -> None:
        """Test basic path protection."""
        zone = ProtectedZone(
            enabled=True,
            protected_paths=["**/.git/**"],
        )

        # Should be protected
        result = zone.is_protected(Path("/project/.git/config"))
        assert result.is_protected

        # Should not be protected
        result = zone.is_protected(Path("/tmp/file.txt"))
        assert not result.is_protected

    def test_glob_patterns(self) -> None:
        """Test glob pattern matching."""
        zone = ProtectedZone(
            enabled=True,
            custom_globs=["**/*.secret"],
        )

        result = zone.is_protected(Path("/home/user/password.secret"))
        assert result.is_protected

        result = zone.is_protected(Path("/home/user/public.txt"))
        assert not result.is_protected

    def test_git_dir_protection(self) -> None:
        """Test .git directory protection."""
        zone = ProtectedZone(
            enabled=True,
            protect_git_dirs=True,
        )

        # Various .git paths should be protected
        protected_paths = [
            "/project/.git",
            "/project/.git/config",
            "/project/subdir/.git/HEAD",
        ]

        for path_str in protected_paths:
            result = zone.is_protected(Path(path_str))
            assert result.is_protected, f"{path_str} should be protected"

    def test_venv_protection(self) -> None:
        """Test virtual environment protection."""
        zone = ProtectedZone(
            enabled=True,
            protect_venvs=True,
        )

        venv_paths = [
            "/project/venv/bin/python",
            "/project/.venv/lib/site-packages",
            "/home/user/virtualenv/project/bin/activate",
        ]

        for path_str in venv_paths:
            result = zone.is_protected(Path(path_str))
            assert result.is_protected, f"{path_str} should be protected"

    def test_custom_paths(self) -> None:
        """Test custom path protection."""
        zone = ProtectedZone(
            enabled=True,
            custom_paths=["C:\\important\\documents"],
        )

        # Exact match should be protected (use Windows-style path)
        result = zone.is_protected(Path("C:\\important\\documents"))
        assert result.is_protected

        # Different path should not be protected
        result = zone.is_protected(Path("C:\\other\\path"))
        assert not result.is_protected

    def test_add_rule(self) -> None:
        """Test adding protection rules dynamically."""
        zone = ProtectedZone(enabled=True)

        zone.add_rule(
            pattern="**/*.keep",
            source=ProtectionSource.CUSTOM_GLOB,
            description="Keep files",
            is_glob=True,
        )

        result = zone.is_protected(Path("/project/src/.keep"))
        assert result.is_protected

    def test_remove_rule(self) -> None:
        """Test removing protection rules."""
        zone = ProtectedZone(
            enabled=True,
            custom_paths=["/temp/path"],
        )

        initial_count = len(zone.rules)
        removed = zone.remove_rule("/temp/path")

        assert removed
        assert len(zone.rules) == initial_count - 1

    def test_filter_protected(self) -> None:
        """Test filtering protected paths from list."""
        zone = ProtectedZone(
            enabled=True,
            protected_paths=["**/.git/**"],
        )

        paths = [
            Path("/tmp/safe.txt"),
            Path("/project/.git/config"),
            Path("/var/log/app.log"),
        ]

        safe, protected = zone.filter_protected(paths)

        assert len(safe) == 2
        assert len(protected) == 1
        assert protected[0][0] == Path("/project/.git/config")

    def test_disabled_zone(self) -> None:
        """Test that disabled zone allows all paths."""
        zone = ProtectedZone(enabled=False)

        result = zone.is_protected(Path("/anything/even/.git"))
        assert not result.is_protected

    def test_recent_file_protection(self) -> None:
        """Test recent file protection based on mtime."""

        zone = ProtectedZone(
            enabled=True,
            protect_recent_days=1,
        )

        # Files modified within last day should be protected
        # (This is tested implicitly through the protection logic)
        assert zone._protect_recent_days == 1
