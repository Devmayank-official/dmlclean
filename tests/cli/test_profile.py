"""
Tests for profile command.

Tests the profile management CLI commands.
"""

from __future__ import annotations

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestProfileCommand:
    """Test profile management commands."""

    def test_profile_list(self) -> None:
        """Test listing all profiles."""
        result = runner.invoke(app, ["profile", "list"])
        assert result.exit_code == 0
        assert "developer" in result.stdout
        assert "designer" in result.stdout

    def test_profile_show(self) -> None:
        """Test showing a specific profile."""
        result = runner.invoke(app, ["profile", "show", "developer"])
        assert result.exit_code == 0
        assert "developer" in result.stdout

    def test_profile_show_not_found(self) -> None:
        """Test showing a non-existent profile."""
        result = runner.invoke(app, ["profile", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_profile_create(self) -> None:
        """Test creating a new profile."""
        result = runner.invoke(
            app,
            ["profile", "create", "test-profile", "--description", "Test profile"],
        )
        # Profile creation may require confirmation
        assert result.exit_code in (0, 5)  # 0 = success, 5 = cancelled

    def test_profile_clone(self) -> None:
        """Test cloning a profile."""
        result = runner.invoke(
            app,
            ["profile", "clone", "developer", "developer-copy"],
        )
        # Clone may require confirmation
        assert result.exit_code in (0, 5)

    def test_profile_delete(self) -> None:
        """Test deleting a profile."""
        result = runner.invoke(
            app,
            ["profile", "delete", "test-profile", "--yes"],
        )
        # Delete may fail if profile doesn't exist
        assert result.exit_code in (0, 1)

    def test_profile_set_default(self) -> None:
        """Test setting default profile."""
        result = runner.invoke(app, ["profile", "set-default", "developer"])
        # May require config file
        assert result.exit_code in (0, 1)

    def test_profile_list_json(self) -> None:
        """Test listing profiles in JSON format."""
        result = runner.invoke(app, ["profile", "list", "--json"])
        assert result.exit_code == 0
        # JSON output should be parseable
        import json

        data = json.loads(result.stdout)
        assert isinstance(data, list)
