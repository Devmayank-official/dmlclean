# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for clean command.

Quick coverage boost for CLI commands.
"""

from unittest.mock import Mock

from typer.testing import CliRunner

from dmlclean.cli.commands.clean import app as clean_app

runner = CliRunner()


class TestCleanCommand:
    """Test clean command."""

    def test_clean_dry_run(self, monkeypatch) -> None:
        """Test clean with dry-run mode."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.files_deleted = 10
        mock_result.size_bytes = 1024000
        mock_service.execute_clean.return_value = mock_result
        monkeypatch.setattr("dmlclean.cli.commands.clean._get_service", lambda: mock_service)

        result = runner.invoke(clean_app, ["--mode", "dry-run"])

        assert result.exit_code == 0
        assert "Preview" in result.output or "Dry-run" in result.output

    def test_clean_with_profile(self, monkeypatch) -> None:
        """Test clean with profile option."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.files_deleted = 5
        mock_result.size_bytes = 512000
        mock_service.execute_clean.return_value = mock_result
        monkeypatch.setattr("dmlclean.cli.commands.clean._get_service", lambda: mock_service)

        result = runner.invoke(clean_app, ["--profile", "developer", "--mode", "dry-run"])

        assert result.exit_code == 0

    def test_clean_invalid_mode(self) -> None:
        """Test clean with invalid mode."""
        result = runner.invoke(clean_app, ["--mode", "invalid"])

        assert result.exit_code != 0
        assert "Invalid mode" in result.output


__all__ = ["TestCleanCommand"]
