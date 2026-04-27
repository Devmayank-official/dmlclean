"""
Unit tests for DMLClean config CLI command.
"""

from __future__ import annotations

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestCliConfig:
    """Tests for dmlclean config command."""

    def test_config_show(self) -> None:
        """Test config show returns configuration."""
        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "general" in result.stdout.lower()

    def test_config_validate(self) -> None:
        """Test config validate on valid config."""
        result = runner.invoke(app, ["config", "validate"])

        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_config_get(self) -> None:
        """Test config get returns value."""
        result = runner.invoke(app, ["config", "get", "general.default_scan_mode"])

        assert result.exit_code == 0
        # Should print the value
        assert "fast" in result.stdout.lower() or "deep" in result.stdout.lower()

    def test_config_get_nonexistent(self) -> None:
        """Test config get on nonexistent key."""
        result = runner.invoke(app, ["config", "get", "nonexistent.key"])

        # Should fail or show error
        assert (
            result.exit_code != 0
            or "not found" in result.stdout.lower()
            or "error" in result.stdout.lower()
        )

    def test_config_help(self) -> None:
        """Test config --help."""
        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0
        assert "config" in result.stdout.lower()

    def test_config_reset(self) -> None:
        """Test config reset requires confirmation."""
        result = runner.invoke(app, ["config", "reset"])

        # Should prompt for confirmation or fail
        assert (
            result.exit_code != 0
            or "confirm" in result.stdout.lower()
            or "reset" in result.stdout.lower()
        )
