# Copyright 2026 DML Labs
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for HistoryService, ProtectionService, and ReportService."""

from __future__ import annotations

from pathlib import Path

from dmlclean.services.history_service import HistoryService
from dmlclean.services.protection_service import ProtectionService
from dmlclean.services.report_service import ReportService
from dmlclean.storage.database import Database

# ============== HistoryService Tests ==============


class TestHistoryService:
    """Tests for HistoryService"""

    def test_list_recent(self, db: Database) -> None:
        """Test listing recent history."""
        service = HistoryService(db)
        service.record_operation(
            id="hist-001",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=100,
            files_deleted=95,
        )
        entries = service.list_recent(limit=10)
        assert len(entries) == 1
        assert entries[0].id == "hist-001"

    def test_get_entry(self, db: Database) -> None:
        """Test getting entry by ID."""
        service = HistoryService(db)
        service.record_operation(id="hist-002", mode="trash", profile="developer", scan_mode="fast")
        entry = service.get_entry("hist-002")
        assert entry is not None
        assert entry.id == "hist-002"

    def test_get_entry_none(self, db: Database) -> None:
        """Test getting non-existent entry."""
        service = HistoryService(db)
        entry = service.get_entry("nonexistent")
        assert entry is None

    def test_get_statistics(self, db: Database) -> None:
        """Test getting statistics."""
        service = HistoryService(db)
        service.record_operation(
            id="hist-003",
            mode="trash",
            profile="developer",
            scan_mode="fast",
            files_found=100,
            files_deleted=95,
            size_bytes=1024 * 1024 * 50,
        )
        stats = service.get_statistics(days=30)
        assert stats["total_files_deleted"] == 95

    def test_clear_history(self, db: Database) -> None:
        """Test clearing history."""
        service = HistoryService(db)
        service.record_operation(id="hist-004", mode="trash", profile="developer", scan_mode="fast")
        service.record_operation(id="hist-005", mode="trash", profile="developer", scan_mode="fast")
        count = service.clear_history()
        assert count >= 2


# ============== ProtectionService Tests ==============


class TestProtectionService:
    """Tests for ProtectionService"""

    def test_add_protection(self, db: Database) -> None:
        """Test adding protected path."""
        service = ProtectionService(db)
        entry = service.add_protection(path="/home/user/important", description="Important files")
        assert entry.path == "/home/user/important"
        assert entry.description == "Important files"

    def test_get_protection(self, db: Database) -> None:
        """Test getting protection by ID."""
        service = ProtectionService(db)
        entry = service.add_protection(path="/home/user/test")
        retrieved = service.get_protection(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id

    def test_get_protection_by_path(self, db: Database) -> None:
        """Test getting protection by path."""
        service = ProtectionService(db)
        service.add_protection(path="/home/user/test")
        retrieved = service.get_protection_by_path("/home/user/test")
        assert retrieved is not None
        assert retrieved.path == "/home/user/test"

    def test_remove_protection(self, db: Database) -> None:
        """Test removing protection."""
        service = ProtectionService(db)
        entry = service.add_protection(path="/home/user/test")
        result = service.remove_protection(entry.id)
        assert result is True
        assert service.get_protection(entry.id) is None

    def test_list_protected(self, db: Database) -> None:
        """Test listing protected paths."""
        service = ProtectionService(db)
        service.add_protection(path="/home/user/test1")
        service.add_protection(path="/home/user/test2")
        entries = service.list_protected()
        assert len(entries) == 2

    def test_check_protection(self, db: Database) -> None:
        """Test checking if path is protected."""
        service = ProtectionService(db)
        service.add_protection(path="/home/user/protected")
        result = service.check_protection("/home/user/protected")
        assert result.is_protected is True

    def test_get_statistics(self, db: Database) -> None:
        """Test getting statistics."""
        service = ProtectionService(db)
        service.add_protection(path="/home/user/path1")
        service.add_protection(path="**/*.glob", is_glob=True)
        stats = service.get_statistics()
        assert stats["total"] == 2
        assert stats["exact_paths"] == 1
        assert stats["glob_patterns"] == 1


# ============== ReportService Tests ==============


class TestReportService:
    """Tests for ReportService"""

    def test_generate_summary(self, db: Database) -> None:
        """Test generating summary report."""
        service = ReportService(db)
        summary = service.generate_summary(days=30)
        assert "total_operations" in summary
        assert "total_files_deleted" in summary

    def test_get_terminal_report(self, db: Database) -> None:
        """Test getting terminal report."""
        service = ReportService(db)
        report = service.get_terminal_report(days=30)
        assert "DMLClean Cleaning Report" in report
        assert "Summary" in report

    def test_export_json(self, db: Database, fs: FakeFilesystem) -> None:
        """Test exporting to JSON."""
        service = ReportService(db)
        output_path = Path("/tmp/report.json")
        count = service.export_json(output_path, days=30)
        assert output_path.exists()
        assert isinstance(count, int)

    def test_export_csv(self, db: Database, fs: FakeFilesystem) -> None:
        """Test exporting to CSV."""
        service = ReportService(db)
        output_path = Path("/tmp/report.csv")
        count = service.export_csv(output_path, days=30)
        assert output_path.exists()
        assert isinstance(count, int)

    def test_export_html(self, db: Database, fs: FakeFilesystem) -> None:
        """Test exporting to HTML."""
        service = ReportService(db)
        output_path = Path("/tmp/report.html")
        count = service.export_html(output_path, days=30)
        assert output_path.exists()
        assert isinstance(count, int)
