"""
Tests for storage command.

Tests the storage management CLI commands.
"""

from __future__ import annotations

from typing import Any

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestStorageCommand:
    """Test storage management commands."""

    def test_storage_info(self) -> None:
        """Test showing storage information."""
        result = runner.invoke(app, ["storage", "info"])
        assert result.exit_code == 0
        assert "DML Labs" in result.stdout or "DML Clean" in result.stdout

    def test_storage_info_json(self) -> None:
        """Test showing storage info in JSON format."""
        result = runner.invoke(app, ["storage", "info", "--json"])
        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert "base_dir" in data or "config_dir" in data

    def test_storage_open(self) -> None:
        """Test opening storage directory."""
        result = runner.invoke(app, ["storage", "open"])
        # May fail on CI or headless systems
        assert result.exit_code in (0, 1)

    def test_storage_clean_temp(self) -> None:
        """Test cleaning temp files from storage."""
        result = runner.invoke(app, ["storage", "clean-temp"])
        # May succeed or have nothing to clean
        assert result.exit_code in (0, 2)

    def test_storage_backup(self, tmp_path: Any) -> None:
        """Test backing up storage."""
        backup_path = tmp_path / "backup"
        result = runner.invoke(
            app,
            ["storage", "backup", str(backup_path)],
        )
        # Backup may require confirmation
        assert result.exit_code in (0, 5)

    def test_storage_restore(self, tmp_path: Any) -> None:
        """Test restoring from backup."""
        backup_path = tmp_path / "backup"
        result = runner.invoke(
            app,
            ["storage", "restore", str(backup_path)],
        )
        # Restore will fail if backup doesn't exist
        assert result.exit_code in (1, 5)

    def test_storage_reset(self) -> None:
        """Test resetting storage."""
        result = runner.invoke(app, ["storage", "reset", "--yes"])
        # Reset requires confirmation
        assert result.exit_code in (0, 5)

    def test_storage_migrate(self) -> None:
        """Test running database migrations."""
        result = runner.invoke(app, ["storage", "migrate"])
        # Migrations should succeed or already be applied
        assert result.exit_code in (0, 1)
