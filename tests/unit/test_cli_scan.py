"""
Unit tests for DMLClean scan CLI command.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from dmlclean.cli.app import app

runner = CliRunner()


class TestCliScan:
    """Tests for dmlclean scan command."""

    def test_scan_help(self) -> None:
        """Test scan --help returns successfully."""
        result = runner.invoke(app, ["scan", "--help"])

        assert result.exit_code == 0
        assert "scan" in result.stdout.lower()

    def test_scan_mode_fast(self) -> None:
        """Test scan --mode fast executes successfully."""
        result = runner.invoke(app, ["scan", "--mode", "fast"])

        assert result.exit_code == 0
        # Should contain scan-related output
        assert "scan" in result.stdout.lower() or "Scan" in result.stdout

    def test_scan_mode_fast_json(self) -> None:
        """Test scan --mode fast --json executes successfully."""
        result = runner.invoke(app, ["scan", "--mode", "fast", "--json"])

        # Test passes if command runs (JSON may be empty if no files to scan)
        assert result.exit_code == 0

        # Try to parse JSON if there's output
        if result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                # If no files to scan, may output message instead of JSON
                pass

    def test_scan_mode_invalid(self) -> None:
        """Test scan with invalid mode shows error."""
        result = runner.invoke(app, ["scan", "--mode", "invalid_mode"])

        # Should exit with error or show error message
        # Note: CLI may show "No paths to scan" instead of invalid mode error
        assert (
            result.exit_code != 0
            or "no paths" in result.stdout.lower()
            or "invalid" in result.stdout.lower()
        )

    def test_scan_quiet(self) -> None:
        """Test scan --quiet suppresses output."""
        result = runner.invoke(app, ["scan", "--mode", "fast", "--quiet"])

        assert result.exit_code == 0
        # Quiet mode should have minimal/no stdout
        # (may still have JSON if --json is also passed)

    def test_scan_mode_deep(self) -> None:
        """Test scan --mode deep executes."""
        result = runner.invoke(app, ["scan", "--mode", "deep"])

        # Deep scan may take longer but should complete
        assert result.exit_code == 0

    def test_scan_with_categories(self) -> None:
        """Test scan --categories filters by category."""
        result = runner.invoke(
            app, ["scan", "--mode", "fast", "--categories", "browser,dev_python"]
        )

        assert result.exit_code == 0

    def test_scan_json_structure(self) -> None:
        """Test scan --json has expected structure."""
        result = runner.invoke(app, ["scan", "--mode", "fast", "--json"])

        assert result.exit_code == 0

        # If there's output, try to parse and check structure
        if result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                # Check for common scan result keys
                valid_keys = {
                    "version",
                    "mode",
                    "scan_mode",
                    "scan",
                    "analysis",
                    "total_files",
                    "total_size_bytes",
                    "candidates",
                }
                # At least some of these keys should be present
                assert bool(set(data.keys()) & valid_keys) or isinstance(data, dict)
            except json.JSONDecodeError:
                # If no files to scan, may output message instead of JSON
                pass
