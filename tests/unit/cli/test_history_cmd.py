# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for history commands.

Covers: history list, show, undo, clear, export
"""

from unittest.mock import Mock, patch

from typer.testing import CliRunner

from dmlclean.cli.commands.history import app as history_app

runner = CliRunner()


class TestHistoryList:
    """Test history list command."""

    def test_history_list_basic(self) -> None:
        """Test basic history list output."""
        with patch("dmlclean.cli.commands.history._get_service") as mock_get_service:
            mock_service = Mock()
            mock_service.list_recent.return_value = []
            mock_get_service.return_value = mock_service

            result = runner.invoke(history_app, ["list"])
            assert result.exit_code == 0

    def test_history_list_with_limit(self) -> None:
        """Test history list with limit."""
        with patch("dmlclean.cli.commands.history._get_service") as mock_get_service:
            mock_service = Mock()
            mock_service.list_recent.return_value = []
            mock_get_service.return_value = mock_service

            result = runner.invoke(history_app, ["list", "--limit", "5"])
            assert result.exit_code == 0

    def test_history_list_invalid_limit(self) -> None:
        """Test history list with invalid limit."""
        result = runner.invoke(history_app, ["list", "--limit", "0"])
        assert result.exit_code != 0
        assert "must be between" in result.output

    def test_history_list_json(self) -> None:
        """Test history list with JSON output."""
        with patch("dmlclean.cli.commands.history._get_service") as mock_get_service:
            mock_service = Mock()
            mock_service.list_recent.return_value = []
            mock_get_service.return_value = mock_service

            result = runner.invoke(history_app, ["list", "--json"])
            assert result.exit_code == 0


class TestHistoryShow:
    """Test history show command."""

    def test_history_show_not_found(self) -> None:
        """Test history show with non-existent ID."""
        with patch("dmlclean.cli.commands.history._get_service") as mock_get_service:
            mock_service = Mock()
            mock_service.get_entry.return_value = None
            mock_get_service.return_value = mock_service

            result = runner.invoke(history_app, ["show", "abc123"])
            assert result.exit_code != 0
            assert "not found" in result.output

    def test_history_show_found(self) -> None:
        """Test history show with existing ID."""
        with patch("dmlclean.cli.commands.history._get_service") as mock_get_service:
            mock_service = Mock()
            mock_entry = Mock()
            mock_entry.to_dict.return_value = {
                "id": "abc123",
                "timestamp": "2026-03-13T10:00:00",
                "mode": "trash",
                "profile": "developer",
                "files_deleted": 100,
                "size_bytes": 1024000,
                "status": "complete",
            }
            mock_service.get_entry.return_value = mock_entry
            mock_get_service.return_value = mock_service

            result = runner.invoke(history_app, ["show", "abc123"])
            assert result.exit_code == 0
            assert "History Entry" in result.output


class TestHistoryUndo:
    """Test history undo command."""

    def test_history_undo_no_entries(self, monkeypatch) -> None:
        """Test undo with no entries."""
        mock_service = Mock()
        mock_service.list_recent.return_value = []
        monkeypatch.setattr("dmlclean.cli.commands.history._get_service", lambda: mock_service)

        result = runner.invoke(history_app, ["undo"])
        # Should exit cleanly with "no operations" message
        assert "No operations to undo" in result.output


class TestHistoryClear:
    """Test history clear command."""

    def test_history_clear_cancelled(self, monkeypatch) -> None:
        """Test history clear cancelled."""
        monkeypatch.setattr("typer.confirm", lambda *args, **kwargs: False)
        result = runner.invoke(history_app, ["clear"])
        # Cancelled is a valid exit (code 0), just no action taken
        assert result.exit_code == 0

    def test_history_clear_confirmed(self) -> None:
        """Test history clear confirmed."""
        with patch("typer.confirm", return_value=True):
            with patch("dmlclean.cli.commands.history._get_service") as mock_get_service:
                mock_service = Mock()
                mock_service.clear_history.return_value = 5
                mock_get_service.return_value = mock_service

                result = runner.invoke(history_app, ["clear"])
                assert result.exit_code == 0
                assert "Cleared" in result.output


class TestHistoryExport:
    """Test history export command."""

    def test_history_export(self) -> None:
        """Test history export."""
        with patch("dmlclean.cli.commands.history._get_service") as mock_get_service:
            mock_service = Mock()
            mock_service.export_history.return_value = 10
            mock_get_service.return_value = mock_service

            result = runner.invoke(history_app, ["export", "test.json"])
            assert result.exit_code == 0
            assert "Exported" in result.output


__all__ = [
    "TestHistoryClear",
    "TestHistoryExport",
    "TestHistoryList",
    "TestHistoryShow",
    "TestHistoryUndo",
]
