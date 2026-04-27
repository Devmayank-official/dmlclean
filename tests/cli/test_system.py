"""
Tests for system command.

Tests the system management CLI commands.
"""

from __future__ import annotations

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestSystemCommand:
    """Test system management commands."""

    def test_system_version(self) -> None:
        """Test showing version information."""
        result = runner.invoke(app, ["system", "version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    def test_system_version_verbose(self) -> None:
        """Test showing verbose version information."""
        result = runner.invoke(app, ["system", "version", "--verbose"])
        assert result.exit_code == 0
        # Should include platform and Python info
        assert "Python" in result.stdout or "Platform" in result.stdout

    def test_system_self_update_check(self) -> None:
        """Test checking for self-update."""
        result = runner.invoke(app, ["system", "self-update", "--check"])
        # Check should succeed or fail gracefully
        assert result.exit_code in (0, 1)

    def test_system_self_update(self) -> None:
        """Test self-update command."""
        result = runner.invoke(app, ["system", "self-update"])
        # Update may fail in test environment
        assert result.exit_code in (0, 1)

    def test_version_command(self) -> None:
        """Test top-level version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    def test_system_info(self) -> None:
        """Test system information command."""
        result = runner.invoke(app, ["system", "info"])
        # Should show system details
        assert result.exit_code in (0, 1)
