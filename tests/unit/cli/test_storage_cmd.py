# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for storage commands.

Covers: storage info, path, open, clean-temp, migrate, backup, restore, reset
"""

from unittest.mock import Mock, patch

from typer.testing import CliRunner

from dmlclean.cli.commands.storage_cmd import app as storage_app

runner = CliRunner()


class TestStorageInfo:
    """Test storage info command."""

    def test_storage_info_basic(self) -> None:
        """Test basic storage info output."""
        result = runner.invoke(storage_app, ["info"])
        assert result.exit_code == 0
        assert "DMLClean Storage Information" in result.output
        assert "Base Directory:" in result.output

    def test_storage_info_json(self) -> None:
        """Test storage info with JSON output."""
        result = runner.invoke(storage_app, ["info", "--json"])
        assert result.exit_code == 0
        assert "{" in result.output


class TestStoragePath:
    """Test storage path command."""

    def test_storage_path_base(self) -> None:
        """Test storage path for base directory."""
        result = runner.invoke(storage_app, ["path", "base"])
        assert result.exit_code == 0
        assert "Base Path:" in result.output

    def test_storage_path_config(self) -> None:
        """Test storage path for config directory."""
        result = runner.invoke(storage_app, ["path", "config"])
        assert result.exit_code == 0
        assert "Config Path:" in result.output

    def test_storage_path_data(self) -> None:
        """Test storage path for data directory."""
        result = runner.invoke(storage_app, ["path", "data"])
        assert result.exit_code == 0
        assert "Data Path:" in result.output

    def test_storage_path_invalid(self) -> None:
        """Test storage path with invalid location."""
        result = runner.invoke(storage_app, ["path", "invalid"])
        assert result.exit_code != 0
        assert "Invalid location" in result.output

    def test_storage_path_db(self) -> None:
        """Test storage path for database file."""
        result = runner.invoke(storage_app, ["path", "db"])
        assert result.exit_code == 0
        assert "Db Path:" in result.output


class TestStorageCleanTemp:
    """Test storage clean-temp command."""

    def test_storage_clean_temp_no_dir(self) -> None:
        """Test clean-temp when temp dir doesn't exist."""
        with patch("dmlclean.cli.commands.storage_cmd.get_cache_dir") as mock_cache:
            from pathlib import Path
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as tmpdir:
                # Point to non-existent temp dir
                mock_cache.return_value = Path(tmpdir)
                result = runner.invoke(storage_app, ["clean-temp"])
                assert result.exit_code == 0


class TestStorageMigrate:
    """Test storage migrate command."""

    def test_storage_migrate_check(self, monkeypatch) -> None:
        """Test migrate check."""
        from dmlclean.storage import database

        mock_db = Mock()
        mock_db.get_migration_version.return_value = "003"
        monkeypatch.setattr(database, "get_database", lambda *args, **kwargs: mock_db)

        result = runner.invoke(storage_app, ["migrate", "--check"])
        assert result.exit_code == 0
        assert "schema version" in result.output


class TestStorageReset:
    """Test storage reset command."""

    def test_storage_reset_cancelled(self, monkeypatch) -> None:
        """Test storage reset cancelled."""
        monkeypatch.setattr("typer.confirm", lambda *args, **kwargs: False)
        result = runner.invoke(storage_app, ["reset"])
        # Cancelled is a valid exit (code 0)
        assert result.exit_code == 0


__all__ = [
    "TestStorageCleanTemp",
    "TestStorageInfo",
    "TestStorageMigrate",
    "TestStoragePath",
    "TestStorageReset",
]
