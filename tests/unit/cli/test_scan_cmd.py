# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for scan command.

Quick coverage boost for CLI commands.
"""

from unittest.mock import Mock

from typer.testing import CliRunner

from dmlclean.cli.commands.scan import app as scan_app

runner = CliRunner()


class TestScanCommand:
    """Test scan command."""

    def test_scan_fast_mode(self, mocker) -> None:
        """Test scan with fast mode."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.total_files = 100
        mock_result.total_size_bytes = 10240000
        mock_result.candidates = 50
        mock_service.execute_scan.return_value = mock_result
        mocker.patch("dmlclean.cli.commands.scan._get_service", return_value=mock_service)

        result = runner.invoke(scan_app, ["--mode", "fast"])

        assert result.exit_code == 0
        assert "Scan" in result.output or "files" in result.output

    def test_scan_deep_mode(self, mocker) -> None:
        """Test scan with deep mode."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.total_files = 200
        mock_result.total_size_bytes = 20480000
        mock_result.candidates = 100
        mock_service.execute_scan.return_value = mock_result
        mocker.patch("dmlclean.cli.commands.scan._get_service", return_value=mock_service)

        result = runner.invoke(scan_app, ["--mode", "deep"])

        assert result.exit_code == 0

    def test_scan_json_output(self, mocker) -> None:
        """Test scan with JSON output."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.to_dict.return_value = {"total_files": 100}
        mock_service.execute_scan.return_value = mock_result
        mocker.patch("dmlclean.cli.commands.scan._get_service", return_value=mock_service)

        result = runner.invoke(scan_app, ["--json"])

        assert result.exit_code == 0
        assert "{" in result.output


__all__ = ["TestScanCommand"]
