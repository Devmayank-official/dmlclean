"""
Integration tests for DMLClean CLI commands.

Tests CLI commands via Typer test client.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from dmlclean.cli.app import app


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


class TestCliCommands:
    """Tests for CLI commands."""

    def test_main_help(self, runner: CliRunner) -> None:
        """Test main help command."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "dmlclean" in result.stdout.lower()
        assert "scan" in result.stdout.lower()
        assert "clean" in result.stdout.lower()

    def test_version(self, runner: CliRunner) -> None:
        """Test version command."""
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "DMLClean" in result.stdout
        assert "Python" in result.stdout

    def test_doctor(self, runner: CliRunner) -> None:
        """Test doctor command."""
        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "DMLClean Doctor" in result.stdout
        assert "Python version" in result.stdout
        assert "Platform" in result.stdout

    def test_config_show(self, runner: CliRunner) -> None:
        """Test config show command."""
        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "general" in result.stdout
        assert "scanner" in result.stdout
        assert "categories" in result.stdout

    def test_config_validate(self, runner: CliRunner) -> None:
        """Test config validate command."""
        result = runner.invoke(app, ["config", "validate"])

        assert result.exit_code == 0
        assert "valid" in result.stdout.lower()

    def test_config_get(self, runner: CliRunner) -> None:
        """Test config get command."""
        result = runner.invoke(app, ["config", "get", "general.default_scan_mode"])

        assert result.exit_code == 0
        assert "fast" in result.stdout

    def test_scan_help(self, runner: CliRunner) -> None:
        """Test scan help."""
        result = runner.invoke(app, ["scan", "--help"])

        assert result.exit_code == 0
        assert "--mode" in result.stdout
        assert "--categories" in result.stdout
        assert "--json" in result.stdout

    def test_clean_help(self, runner: CliRunner) -> None:
        """Test clean help."""
        result = runner.invoke(app, ["clean", "--help"])

        assert result.exit_code == 0
        # Clean is a Typer group with subcommands
        assert "clean" in result.stdout.lower()
        assert "execute" in result.stdout.lower()

    def test_protect_help(self, runner: CliRunner) -> None:
        """Test protect help."""
        result = runner.invoke(app, ["protect", "--help"])

        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "remove" in result.stdout
        assert "list" in result.stdout

    def test_history_help(self, runner: CliRunner) -> None:
        """Test history help."""
        result = runner.invoke(app, ["history", "--help"])

        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "undo" in result.stdout

    def test_report_help(self, runner: CliRunner) -> None:
        """Test report help."""
        result = runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0
        # Report is a Typer group with subcommands
        assert "report" in result.stdout.lower()
        assert "generate" in result.stdout.lower()

    def test_schedule_help(self, runner: CliRunner) -> None:
        """Test schedule help."""
        result = runner.invoke(app, ["schedule", "--help"])

        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "list" in result.stdout
        assert "remove" in result.stdout

    def test_unknown_command(self, runner: CliRunner) -> None:
        """Test unknown command handling."""
        result = runner.invoke(app, ["unknown-command"])

        assert result.exit_code != 0
        # Error message may vary, just check for non-zero exit
        assert result.exit_code == 2

    def test_verbose_flag(self, runner: CliRunner) -> None:
        """Test verbose flag."""
        result = runner.invoke(app, ["--verbose", "doctor"])

        assert result.exit_code == 0
        # Verbose should show more logging

    def test_quiet_flag(self, runner: CliRunner) -> None:
        """Test quiet flag."""
        result = runner.invoke(app, ["--quiet", "version"])

        # Quiet should suppress most output
        assert result.exit_code == 0


class TestCliExitCodes:
    """Tests for CLI exit codes."""

    def test_success_exit_code(self, runner: CliRunner) -> None:
        """Test success returns exit code 0."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_invalid_command_exit_code(self, runner: CliRunner) -> None:
        """Test invalid command returns non-zero."""
        result = runner.invoke(app, ["nonexistent"])
        assert result.exit_code != 0

    def test_config_invalid_key_exit_code(self, runner: CliRunner) -> None:
        """Test invalid config key returns error."""
        result = runner.invoke(app, ["config", "get", "invalid.key"])
        assert result.exit_code != 0
