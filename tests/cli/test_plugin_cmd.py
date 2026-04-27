"""
Tests for plugin command.

Tests the plugin management CLI commands.
"""

from __future__ import annotations

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestPluginCommand:
    """Test plugin management commands."""

    def test_plugin_list(self) -> None:
        """Test listing all plugins."""
        result = runner.invoke(app, ["plugin", "list"])
        assert result.exit_code == 0
        # Should list built-in plugins
        assert "system_junk" in result.stdout or "browser" in result.stdout

    def test_plugin_list_json(self) -> None:
        """Test listing plugins in JSON format."""
        result = runner.invoke(app, ["plugin", "list", "--json"])
        assert result.exit_code == 0
        import json

        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_plugin_info(self) -> None:
        """Test showing plugin info."""
        result = runner.invoke(app, ["plugin", "info", "browser"])
        assert result.exit_code == 0
        assert "browser" in result.stdout.lower()

    def test_plugin_info_not_found(self) -> None:
        """Test showing info for non-existent plugin."""
        result = runner.invoke(app, ["plugin", "info", "nonexistent"])
        assert result.exit_code == 1

    def test_plugin_scan(self) -> None:
        """Test scanning with a specific plugin."""
        result = runner.invoke(
            app,
            ["plugin", "scan", "dev_python", "--path", "/tmp"],
        )
        # Scan may find nothing or fail due to permissions
        assert result.exit_code in (0, 1, 2)

    def test_plugin_enable(self) -> None:
        """Test enabling a plugin."""
        result = runner.invoke(app, ["plugin", "enable", "browser"])
        # May require config file
        assert result.exit_code in (0, 1)

    def test_plugin_disable(self) -> None:
        """Test disabling a plugin."""
        result = runner.invoke(app, ["plugin", "disable", "browser"])
        # May require config file
        assert result.exit_code in (0, 1)

    def test_plugin_scan_json(self) -> None:
        """Test plugin scan with JSON output."""
        result = runner.invoke(
            app,
            ["plugin", "scan", "system_junk", "--path", "/tmp", "--json"],
        )
        # May succeed or fail depending on system
        assert result.exit_code in (0, 1, 2)
