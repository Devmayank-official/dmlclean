# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""
Tests for DMLClean Reports module.

Tests cover:
- Terminal reporter
- Report exporters (JSON, CSV, HTML)
- History reporter
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from dmlclean.reports.exporter import (
    CSVExporter,
    ExportError,
    HTMLExporter,
    JSONExporter,
    get_exporter,
)
from dmlclean.reports.history import CleaningStats, HistoryReporter, TrendData
from dmlclean.reports.terminal import TerminalReporter


class TestTerminalReporter:
    """Tests for TerminalReporter class."""

    def test_init_default(self) -> None:
        """Test TerminalReporter initialization with defaults."""
        reporter = TerminalReporter()
        assert reporter.console is not None
        assert reporter.width is None

    def test_init_custom(self) -> None:
        """Test TerminalReporter initialization with custom parameters."""
        from rich.console import Console

        custom_console = Console()
        reporter = TerminalReporter(console=custom_console, width=80)
        assert reporter.console is custom_console
        assert reporter.width == 80

    def test_render_preview(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test rendering preview of files to be cleaned."""
        from dmlclean.core.analyzer import CleanCandidate, RiskLevel

        reporter = TerminalReporter()

        # Create test candidates
        candidates = [
            CleanCandidate(
                path=Path("/tmp/test1.tmp"),
                category="system_junk",
                size_bytes=1024,
                risk_level=RiskLevel.LOW,
                reason="Test file",
            ),
            CleanCandidate(
                path=Path("/tmp/test2.tmp"),
                category="system_junk",
                size_bytes=2048,
                risk_level=RiskLevel.LOW,
                reason="Test file",
            ),
        ]

        reporter.render_preview(candidates, 3072)
        captured = capsys.readouterr()
        assert "Preview" in captured.out
        assert "Files to Clean" in captured.out

    def test_print_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing success message."""
        reporter = TerminalReporter()
        reporter.print_success("Operation completed", "Success")
        captured = capsys.readouterr()
        assert "Success" in captured.out
        assert "Operation completed" in captured.out

    def test_print_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing error message."""
        reporter = TerminalReporter()
        reporter.print_error("Something went wrong", "Error")
        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "Something went wrong" in captured.out

    def test_print_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing warning message."""
        reporter = TerminalReporter()
        reporter.print_warning("Be careful", "Warning")
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "Be careful" in captured.out

    def test_print_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test printing info message."""
        reporter = TerminalReporter()
        reporter.print_info("Just so you know", "Info")
        captured = capsys.readouterr()
        assert "Info" in captured.out
        assert "Just so you know" in captured.out


class TestJSONExporter:
    """Tests for JSONExporter class."""

    def test_init_default(self) -> None:
        """Test JSONExporter initialization with defaults."""
        exporter = JSONExporter()
        assert exporter.indent == 2
        assert exporter.ensure_ascii is False

    def test_init_custom(self) -> None:
        """Test JSONExporter initialization with custom parameters."""
        exporter = JSONExporter(indent=4, ensure_ascii=True)
        assert exporter.indent == 4
        assert exporter.ensure_ascii is True

    def test_export_simple_dict(self) -> None:
        """Test exporting simple dictionary."""
        exporter = JSONExporter()
        data = {"key": "value", "number": 42}
        result = exporter.export(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_export_nested_dict(self) -> None:
        """Test exporting nested dictionary."""
        exporter = JSONExporter()
        data = {
            "outer": {
                "inner": {"value": "test"},
                "list": [1, 2, 3],
            }
        }
        result = exporter.export(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_export_with_datetime(self) -> None:
        """Test exporting dictionary with datetime."""
        exporter = JSONExporter()
        test_datetime = datetime(2026, 3, 13, 10, 30, 0)
        data = {"timestamp": test_datetime}
        result = exporter.export(data)
        parsed = json.loads(result)
        assert "2026-03-13T10:30:00" in parsed["timestamp"]

    def test_export_to_file(self, tmp_path: Path) -> None:
        """Test exporting to file."""
        exporter = JSONExporter()
        data = {"test": "data"}
        output_file = tmp_path / "test.json"

        result_path = exporter.export_to_file(data, output_file)
        assert result_path == output_file
        assert output_file.exists()

        content = output_file.read_text()
        parsed = json.loads(content)
        assert parsed == data

    def test_export_empty_dict(self) -> None:
        """Test exporting empty dictionary."""
        exporter = JSONExporter()
        data: dict[str, Any] = {}
        result = exporter.export(data)
        parsed = json.loads(result)
        assert parsed == {}

    def test_export_error(self) -> None:
        """Test export error handling."""
        exporter = JSONExporter()
        # Create circular reference
        data: dict[str, Any] = {"test": None}
        data["circular"] = data

        with pytest.raises(ExportError):
            exporter.export(data)


class TestCSVExporter:
    """Tests for CSVExporter class."""

    def test_init_default(self) -> None:
        """Test CSVExporter initialization with defaults."""
        exporter = CSVExporter()
        assert exporter.delimiter == ","
        assert exporter.quoting == 0  # csv.QUOTE_MINIMAL

    def test_init_custom(self) -> None:
        """Test CSVExporter initialization with custom parameters."""
        import csv

        exporter = CSVExporter(delimiter=";", quoting=csv.QUOTE_ALL)
        assert exporter.delimiter == ";"
        assert exporter.quoting == csv.QUOTE_ALL

    def test_export_list_of_dicts(self) -> None:
        """Test exporting list of dictionaries."""
        exporter = CSVExporter()
        data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]
        result = exporter.export(data)
        assert "name,age" in result
        assert "Alice,30" in result
        assert "Bob,25" in result

    def test_export_empty_list(self) -> None:
        """Test exporting empty list."""
        exporter = CSVExporter()
        data: list[dict[str, Any]] = []
        result = exporter.export(data)
        assert result == ""

    def test_export_dict_with_rows(self) -> None:
        """Test exporting dictionary with rows and columns."""
        exporter = CSVExporter()
        data = {
            "columns": ["name", "value"],
            "rows": [
                {"name": "test1", "value": "100"},
                {"name": "test2", "value": "200"},
            ],
        }
        result = exporter.export(data)
        assert "name,value" in result
        assert "test1,100" in result

    def test_export_simple_key_value(self) -> None:
        """Test exporting simple key-value pairs."""
        exporter = CSVExporter()
        data = {"key1": "value1", "key2": "value2"}
        result = exporter.export(data)
        assert "Key,Value" in result
        assert "key1,value1" in result

    def test_export_to_file(self, tmp_path: Path) -> None:
        """Test exporting to file."""
        exporter = CSVExporter()
        data = [{"name": "test", "value": "100"}]
        output_file = tmp_path / "test.csv"

        result_path = exporter.export_to_file(data, output_file)
        assert result_path == output_file
        assert output_file.exists()

        content = output_file.read_text()
        assert "name,value" in content


class TestHTMLExporter:
    """Tests for HTMLExporter class."""

    def test_init_default(self) -> None:
        """Test HTMLExporter initialization with defaults."""
        exporter = HTMLExporter()
        assert exporter.title == "DMLClean Report"
        assert exporter.include_css is True

    def test_init_custom(self) -> None:
        """Test HTMLExporter initialization with custom parameters."""
        exporter = HTMLExporter(title="Custom Report", include_css=False)
        assert exporter.title == "Custom Report"
        assert exporter.include_css is False

    def test_export_basic(self) -> None:
        """Test basic HTML export."""
        exporter = HTMLExporter()
        data = {"key": "value"}
        result = exporter.export(data)

        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "<title>DMLClean Report</title>" in result
        assert "</html>" in result

    def test_export_with_css(self) -> None:
        """Test HTML export with CSS."""
        exporter = HTMLExporter(include_css=True)
        data = {"test": "data"}
        result = exporter.export(data)

        assert "<style>" in result
        assert "body {" in result

    def test_export_without_css(self) -> None:
        """Test HTML export without CSS."""
        exporter = HTMLExporter(include_css=False)
        data = {"test": "data"}
        result = exporter.export(data)

        assert "<style>" not in result

    def test_export_dict_section(self) -> None:
        """Test exporting dictionary as HTML section."""
        exporter = HTMLExporter()
        data = {"category": "system_junk", "files": "100", "size": "50 MB"}
        result = exporter.export(data)

        # Check for HTML structure (flexible assertions)
        assert "<table>" in result or "<div" in result
        assert "category" in result.lower() or "Category" in result

    def test_export_list_section(self) -> None:
        """Test exporting list as HTML section."""
        exporter = HTMLExporter()
        # List of dicts works directly
        data = [
            {"name": "file1.txt", "size": "10 KB"},
            {"name": "file2.txt", "size": "20 KB"},
        ]
        result = exporter.export(data)

        # Check for HTML structure
        assert "<!DOCTYPE html>" in result
        assert "<html" in result

    def test_export_to_file(self, tmp_path: Path) -> None:
        """Test exporting to file."""
        exporter = HTMLExporter()
        data = {"test": "data"}
        output_file = tmp_path / "report.html"

        result_path = exporter.export_to_file(data, output_file)
        assert result_path == output_file
        assert output_file.exists()

        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content


class TestGetExporter:
    """Tests for get_exporter factory function."""

    def test_get_json_exporter(self) -> None:
        """Test getting JSON exporter."""
        exporter = get_exporter("json")
        assert isinstance(exporter, JSONExporter)

    def test_get_csv_exporter(self) -> None:
        """Test getting CSV exporter."""
        exporter = get_exporter("csv")
        assert isinstance(exporter, CSVExporter)

    def test_get_html_exporter(self) -> None:
        """Test getting HTML exporter."""
        exporter = get_exporter("html")
        assert isinstance(exporter, HTMLExporter)

    def test_get_exporter_case_insensitive(self) -> None:
        """Test exporter lookup is case insensitive."""
        assert isinstance(get_exporter("JSON"), JSONExporter)
        assert isinstance(get_exporter("Csv"), CSVExporter)
        assert isinstance(get_exporter("HTML"), HTMLExporter)

    def test_get_exporter_invalid(self) -> None:
        """Test getting invalid exporter."""
        with pytest.raises(ExportError) as exc_info:
            get_exporter("xml")
        assert "Unsupported export format" in str(exc_info.value)


class TestCleaningStats:
    """Tests for CleaningStats dataclass."""

    def test_init_default(self) -> None:
        """Test CleaningStats initialization with defaults."""
        stats = CleaningStats()
        assert stats.total_operations == 0
        assert stats.total_files_deleted == 0
        assert stats.total_size_freed == 0
        assert stats.top_categories == {}

    def test_to_dict(self) -> None:
        """Test converting stats to dictionary."""
        stats = CleaningStats(
            total_operations=10,
            successful_operations=8,
            failed_operations=2,
            total_files_deleted=150,
            total_size_freed=1024 * 1024 * 50,  # 50 MB
            avg_files_per_operation=15.0,
            avg_size_per_operation=1024 * 1024 * 5,  # 5 MB
            first_operation=datetime(2026, 1, 1),
            last_operation=datetime(2026, 3, 13),
            most_used_mode="trash",
            most_used_profile="developer",
            top_categories={"system_junk": 100, "browser": 50},
        )

        result = stats.to_dict()
        assert result["total_operations"] == 10
        assert result["total_size_freed_human"] == "50.00 MB"
        assert "top_categories" in result


class TestTrendData:
    """Tests for TrendData dataclass."""

    def test_init_default(self) -> None:
        """Test TrendData initialization with defaults."""
        trend = TrendData(date=datetime.now())
        assert trend.operations_count == 0
        assert trend.files_deleted == 0
        assert trend.size_freed == 0

    def test_to_dict(self) -> None:
        """Test converting trend data to dictionary."""
        test_date = datetime(2026, 3, 13)
        trend = TrendData(
            date=test_date,
            operations_count=5,
            files_deleted=100,
            size_freed=1024 * 1024 * 10,  # 10 MB
        )

        result = trend.to_dict()
        assert result["date"] == "2026-03-13"
        assert result["operations_count"] == 5
        assert result["size_freed_human"] == "10.00 MB"


class TestHistoryReporter:
    """Tests for HistoryReporter class."""

    def test_init(self, db: Any, history_repo: Any) -> None:
        """Test HistoryReporter initialization."""

        reporter = HistoryReporter(db, history_repo)
        assert reporter.db == db
        assert reporter.history_repo == history_repo

    def test_get_summary_stats_empty(self, db: Any, history_repo: Any) -> None:
        """Test getting summary stats with no data."""

        reporter = HistoryReporter(db, history_repo)
        stats = reporter.get_summary_stats()

        assert stats.total_operations == 0
        assert stats.total_files_deleted == 0

    def test_get_trend_data_empty(self, db: Any, history_repo: Any) -> None:
        """Test getting trend data with no data."""

        reporter = HistoryReporter(db, history_repo)
        trends = reporter.get_trend_data(days=30)

        assert trends == []

    def test_get_category_breakdown_empty(self, db: Any, history_repo: Any) -> None:
        """Test getting category breakdown with no data."""

        reporter = HistoryReporter(db, history_repo)
        breakdown = reporter.get_category_breakdown()

        assert breakdown == {}

    def test_generate_report(self, db: Any, history_repo: Any) -> None:
        """Test generating comprehensive report."""

        reporter = HistoryReporter(db, history_repo)
        report = reporter.generate_report(days=30)

        assert "generated_at" in report
        assert "period_days" in report
        assert "summary" in report
        assert isinstance(report["summary"], dict)


__all__ = [
    "TestCSVExporter",
    "TestCleaningStats",
    "TestGetExporter",
    "TestHTMLExporter",
    "TestHistoryReporter",
    "TestJSONExporter",
    "TestTerminalReporter",
    "TestTrendData",
]
