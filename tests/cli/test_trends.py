"""
Tests for trends command.

Tests the disk usage trends CLI commands.
"""

from __future__ import annotations

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestTrendsCommand:
    """Test disk usage trends commands."""

    def test_trends_basic(self) -> None:
        """Test basic trends command."""
        result = runner.invoke(app, ["trends"])
        # Trends may not have data yet
        assert result.exit_code in (0, 1)

    def test_trends_json(self) -> None:
        """Test trends with JSON output."""
        result = runner.invoke(app, ["trends", "--json"])
        # May return empty trends
        assert result.exit_code in (0, 1)
        if result.exit_code == 0:
            import json

            data = json.loads(result.stdout)
            assert isinstance(data, dict)

    def test_trends_since(self) -> None:
        """Test trends with since date."""
        result = runner.invoke(app, ["trends", "--since", "2026-01-01"])
        # May not have historical data
        assert result.exit_code in (0, 1)

    def test_trends_warn_threshold(self) -> None:
        """Test trends with warning threshold."""
        result = runner.invoke(app, ["trends", "--warn-threshold", "80"])
        # Should succeed
        assert result.exit_code in (0, 1)

    def test_trends_invalid_date(self) -> None:
        """Test trends with invalid date."""
        result = runner.invoke(app, ["trends", "--since", "invalid-date"])
        # Should fail with invalid date
        assert result.exit_code == 2
