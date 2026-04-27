# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for protect command.

Quick coverage boost for CLI commands.
"""

from unittest.mock import Mock

from typer.testing import CliRunner

from dmlclean.cli.commands.protect import app as protect_app

runner = CliRunner()


class TestProtectCommand:
    """Test protect command."""

    def test_protect_add(self, mocker) -> None:
        """Test adding protected path."""
        mock_service = Mock()
        mock_entry = Mock()
        mock_entry.id = "test-id"
        mock_entry.path = "/test/path"
        mock_service.add_protection.return_value = mock_entry
        mocker.patch("dmlclean.cli.commands.protect._get_service", return_value=mock_service)

        result = runner.invoke(protect_app, ["add", "/test/path", "-d", "Test"])

        assert result.exit_code == 0
        assert "Protected" in result.output or "Added" in result.output

    def test_protect_list(self, mocker) -> None:
        """Test listing protected paths."""
        mock_service = Mock()
        mock_entry = Mock()
        mock_entry.id = "test-id"
        mock_entry.path = "/test/path"
        mock_entry.is_glob = False
        mock_entry.description = "Test"
        mock_service.list_protected.return_value = [mock_entry]
        mocker.patch("dmlclean.cli.commands.protect._get_service", return_value=mock_service)

        result = runner.invoke(protect_app, ["list"])

        assert result.exit_code == 0

    def test_protect_check(self, mocker) -> None:
        """Test checking if path is protected."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.is_protected = True
        mock_result.reason = "Test reason"
        mock_service.check_protection.return_value = mock_result
        mocker.patch("dmlclean.cli.commands.protect._get_service", return_value=mock_service)

        result = runner.invoke(protect_app, ["check", "-p", "/test/path"])

        assert result.exit_code == 0
        assert "PROTECTED" in result.output or "protected" in result.output


__all__ = ["TestProtectCommand"]
