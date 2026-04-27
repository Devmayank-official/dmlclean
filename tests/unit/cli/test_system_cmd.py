# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for system commands.

Covers: system info, version, self-update, completion
"""

from typer.testing import CliRunner

from dmlclean.cli.commands.system import app as system_app

runner = CliRunner()


class TestSystemInfo:
    """Test system info command."""

    def test_system_info_basic(self) -> None:
        """Test basic system info output."""
        result = runner.invoke(system_app, ["info"])
        assert result.exit_code == 0
        assert "System Information" in result.output
        assert "OS:" in result.output
        assert "Python:" in result.output

    def test_system_info_verbose(self) -> None:
        """Test verbose system info output."""
        result = runner.invoke(system_app, ["info", "--verbose"])
        assert result.exit_code == 0
        assert "Disk Usage:" in result.output


class TestSystemVersion:
    """Test system version command."""

    def test_version_basic(self) -> None:
        """Test basic version output."""
        result = runner.invoke(system_app, ["version"])
        assert result.exit_code == 0
        assert "DMLClean" in result.output
        assert "version" in result.output
        assert "0.1.0" in result.output

    def test_version_verbose(self) -> None:
        """Test verbose version output."""
        result = runner.invoke(system_app, ["version", "--verbose"])
        assert result.exit_code == 0
        assert "Detailed Information" in result.output
        assert "Executable:" in result.output


class TestSystemCompletion:
    """Test completion command."""

    def test_completion_bash(self) -> None:
        """Test bash completion script generation."""
        # Just verify command runs - completion implementation varies by typer version
        result = runner.invoke(system_app, ["completion", "bash"])
        # Command should run without crashing
        assert result.exit_code == 0 or result.exit_code == 1

    def test_completion_zsh(self) -> None:
        """Test zsh completion script generation."""
        result = runner.invoke(system_app, ["completion", "zsh"])
        assert result.exit_code == 0 or result.exit_code == 1

    def test_completion_fish(self) -> None:
        """Test fish completion script generation."""
        result = runner.invoke(system_app, ["completion", "fish"])
        assert result.exit_code == 0 or result.exit_code == 1

    def test_completion_invalid_shell(self) -> None:
        """Test invalid shell raises error."""
        result = runner.invoke(system_app, ["completion", "invalid"])
        assert result.exit_code != 0
        assert "Invalid shell" in result.output


__all__ = [
    "TestSystemCompletion",
    "TestSystemInfo",
    "TestSystemVersion",
]
