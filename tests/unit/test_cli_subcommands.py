"""
Unit tests for DMLClean CLI subcommands.

Tests protect, history, report, and schedule commands.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestCliProtectSubcommand:
    """Tests for dmlclean protect subcommand."""

    def test_protect_help(self) -> None:
        """Test protect --help returns successfully."""
        result = runner.invoke(app, ["protect", "--help"])
        assert result.exit_code == 0
        assert "protect" in result.stdout.lower()

    @patch("dmlclean.cli.commands.protect.ProtectionService")
    def test_protect_add_path(self, mock_service_cls: MagicMock) -> None:
        """Test protect add command."""
        mock_service = MagicMock()
        mock_service.add_protection.return_value = MagicMock(
            id="test-123",
            path="/important/path",
            is_glob=False,
            description="",
        )
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["protect", "add", "/important/path"])

        assert result.exit_code == 0
        assert "Added to Protected Zone" in result.stdout

    @patch("dmlclean.cli.commands.protect.ProtectionService")
    def test_protect_add_glob(self, mock_service_cls: MagicMock) -> None:
        """Test protect add with --glob flag."""
        mock_service = MagicMock()
        mock_service.add_protection.return_value = MagicMock(
            id="test-123",
            path="**/*.important",
            is_glob=True,
            description="",
        )
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["protect", "add", "--glob", "**/*.important"])

        assert result.exit_code == 0

    @patch("dmlclean.cli.commands.protect.ProtectionService")
    def test_protect_remove(self, mock_service_cls: MagicMock) -> None:
        """Test protect remove command."""
        mock_service = MagicMock()
        mock_service.get_protection.return_value = MagicMock(
            id="test-123",
            path="/path/to/remove",
        )
        mock_service.remove_protection.return_value = True
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["protect", "remove", "/path/to/remove"])

        assert result.exit_code == 0
        assert "Removed from Protected Zone" in result.stdout

    @patch("dmlclean.cli.commands.protect.ProtectionService")
    def test_protect_list(self, mock_service_cls: MagicMock) -> None:
        """Test protect list command."""
        mock_service = MagicMock()
        mock_service.list_protected.return_value = [
            MagicMock(id="1", path="/system/protected", is_glob=False, description=""),
            MagicMock(id="2", path="/user/protected", is_glob=False, description=""),
        ]
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["protect", "list"])

        assert result.exit_code == 0

    @patch("dmlclean.cli.commands.protect.ProtectionService")
    def test_protect_list_empty(self, mock_service_cls: MagicMock) -> None:
        """Test protect list when empty."""
        mock_service = MagicMock()
        mock_service.list_protected.return_value = []
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["protect", "list"])

        assert result.exit_code == 0
        assert "No protected paths" in result.stdout

    @patch("dmlclean.cli.commands.protect.ProtectionService")
    def test_protect_check_protected(self, mock_service_cls: MagicMock) -> None:
        """Test protect check command for protected path."""
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.is_protected = True
        mock_result.reason = "Built-in protected path"
        mock_service.check_protection.return_value = mock_result
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["protect", "check", "/protected/path"])

        assert result.exit_code == 0
        assert "PROTECTED" in result.stdout

    @patch("dmlclean.cli.commands.protect.ProtectionService")
    def test_protect_check_not_protected(self, mock_service_cls: MagicMock) -> None:
        """Test protect check command for non-protected path."""
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.is_protected = False
        mock_service.check_protection.return_value = mock_result
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["protect", "check", "/normal/path"])

        assert result.exit_code == 0
        assert "NOT PROTECTED" in result.stdout


class TestCliHistorySubcommand:
    """Tests for dmlclean history subcommand."""

    def test_history_help(self) -> None:
        """Test history --help returns successfully."""
        result = runner.invoke(app, ["history", "--help"])
        assert result.exit_code == 0
        assert "history" in result.stdout.lower()

    @patch("dmlclean.cli.commands.history.HistoryService")
    def test_history_list(self, mock_service_cls: MagicMock) -> None:
        """Test history list command."""
        mock_service = MagicMock()
        mock_service.list_recent.return_value = [
            MagicMock(
                id="abc123",
                timestamp="2026-03-11T00:00:00",
                mode="trash",
                files_deleted=100,
                size_bytes=1024 * 1024 * 50,
                profile="developer",
            )
        ]
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["history", "list"])

        assert result.exit_code == 0

    @patch("dmlclean.cli.commands.history.HistoryService")
    def test_history_list_empty(self, mock_service_cls: MagicMock) -> None:
        """Test history list when empty."""
        mock_service = MagicMock()
        mock_service.list_recent.return_value = []
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["history", "list"])

        assert result.exit_code == 0
        assert "No cleaning history" in result.stdout

    @patch("dmlclean.cli.commands.history.HistoryService")
    def test_history_undo_yes(self, mock_service_cls: MagicMock) -> None:
        """Test history undo with --yes flag."""
        mock_service = MagicMock()
        mock_service.list_recent.return_value = [
            MagicMock(
                id="abc123",
                timestamp="2026-03-11T00:00:00",
                mode="trash",
                files_deleted=100,
                size_bytes=1024 * 1024 * 50,
                profile="developer",
            )
        ]
        mock_service.undo_entry.return_value = {
            "success": True,
            "total_restored": 100,
            "total_failed": 0,
        }
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["history", "undo", "--yes"])

        assert result.exit_code == 0

    @patch("dmlclean.cli.commands.history.HistoryService")
    def test_history_clear_yes(self, mock_service_cls: MagicMock) -> None:
        """Test history clear with --yes flag."""
        mock_service = MagicMock()
        mock_service.clear_history.return_value = 10
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["history", "clear", "--yes"])

        assert result.exit_code == 0

    @patch("dmlclean.cli.commands.history.HistoryService")
    def test_history_export(self, mock_service_cls: MagicMock) -> None:
        """Test history export command."""
        mock_service = MagicMock()
        mock_service.export_history.return_value = 10
        mock_service_cls.return_value = mock_service

        result = runner.invoke(app, ["history", "export", "/tmp/test.json"])

        assert result.exit_code == 0


class TestCliReportSubcommand:
    """Tests for dmlclean report subcommand."""

    def test_report_help(self) -> None:
        """Test report --help returns successfully."""
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
        assert "report" in result.stdout.lower()


class TestCliScheduleSubcommand:
    """Tests for dmlclean schedule subcommand."""

    def test_schedule_help(self) -> None:
        """Test schedule --help returns successfully."""
        result = runner.invoke(app, ["schedule", "--help"])
        assert result.exit_code == 0
        assert "schedule" in result.stdout.lower()
